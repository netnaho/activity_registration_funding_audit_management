from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import APIError
from app.models.enums import RegistrationStatus, UserRole
from app.models.material_checklist import MaterialChecklistItem
from app.models.review_workflow_record import ReviewWorkflowRecord
from app.models.material_version import MaterialVersion
from app.models.registration_form import RegistrationForm
from app.models.registration_material_submission import RegistrationMaterialSubmission
from app.models.supplementary_submission_record import SupplementarySubmissionRecord
from app.models.user import User
from app.models.enums import MaterialStatus
from app.utils.masking import mask_contact, mask_id_number


MAX_TOTAL_UPLOAD_SIZE = 200 * 1024 * 1024


def assert_registration_actor_access(
    *,
    registration: RegistrationForm,
    actor: User,
    allow_reviewer_admin: bool = True,
) -> None:
    if actor.role == UserRole.APPLICANT:
        if registration.applicant_id != actor.id:
            raise APIError(403, "Forbidden resource access")
        return

    if allow_reviewer_admin and actor.role in {UserRole.REVIEWER, UserRole.SYSTEM_ADMIN}:
        return

    raise APIError(403, "Forbidden resource access")


def create_registration(
    db: Session,
    *,
    applicant: User,
    title: str,
    description: str,
    contact_phone: str,
    id_number: str,
    deadline_at: datetime,
) -> RegistrationForm:
    if applicant.role != UserRole.APPLICANT:
        raise APIError(403, "Only applicants can create registration")

    if deadline_at <= datetime.now(timezone.utc):
        raise APIError(400, "Deadline must be in the future")

    record = RegistrationForm(
        applicant_id=applicant.id,
        title=title,
        description=description,
        contact_phone=contact_phone,
        id_number=id_number,
        deadline_at=deadline_at,
        status=RegistrationStatus.DRAFT,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def _registration_total_size(db: Session, registration_id: int) -> int:
    total = db.scalar(
        select(func.coalesce(func.sum(MaterialVersion.file_size_bytes), 0))
        .join(RegistrationMaterialSubmission, MaterialVersion.submission_id == RegistrationMaterialSubmission.id)
        .where(RegistrationMaterialSubmission.registration_form_id == registration_id)
    )
    return int(total or 0)


def ensure_registration_upload_limit(db: Session, registration_id: int, new_file_size: int) -> None:
    total = _registration_total_size(db, registration_id)
    if total + new_file_size > MAX_TOTAL_UPLOAD_SIZE:
        raise APIError(400, "Total uploaded size exceeds 200MB limit")


def _required_item_ids(db: Session) -> set[int]:
    rows = db.scalars(select(MaterialChecklistItem.id).where(MaterialChecklistItem.required.is_(True))).all()
    return set(rows)


def _submitted_item_ids(db: Session, registration_id: int) -> set[int]:
    rows = db.execute(
        select(RegistrationMaterialSubmission.checklist_item_id)
        .join(MaterialVersion, MaterialVersion.submission_id == RegistrationMaterialSubmission.id)
        .where(
            RegistrationMaterialSubmission.registration_form_id == registration_id,
            MaterialVersion.status.in_(
                [MaterialStatus.SUBMITTED, MaterialStatus.NEEDS_CORRECTION, MaterialStatus.PENDING_SUBMISSION]
            ),
        )
    ).all()
    return {row[0] for row in rows}


def submit_registration(db: Session, registration_id: int, applicant: User) -> RegistrationForm:
    registration = db.scalar(select(RegistrationForm).where(RegistrationForm.id == registration_id))
    if not registration:
        raise APIError(404, "Registration not found")
    if registration.applicant_id != applicant.id:
        raise APIError(403, "Cannot submit another applicant registration")
    if registration.is_locked:
        raise APIError(400, "Registration is locked")

    required = _required_item_ids(db)
    submitted = _submitted_item_ids(db, registration_id)
    missing = required - submitted
    if missing:
        raise APIError(400, "Checklist mandatory materials are incomplete")

    registration.status = RegistrationStatus.SUBMITTED
    registration.submitted_at = datetime.now(timezone.utc)
    db.commit()
    from app.services.material_service import mark_pending_versions_submitted

    mark_pending_versions_submitted(db, registration_id)
    db.refresh(registration)
    return registration


def maybe_lock_registration(registration: RegistrationForm) -> bool:
    if registration.deadline_at and registration.deadline_at <= datetime.now(timezone.utc):
        registration.is_locked = True
        return True
    return False


def create_supplementary_window(db: Session, registration: RegistrationForm, requested_by: User, reason: str) -> SupplementarySubmissionRecord:
    assert_registration_actor_access(registration=registration, actor=requested_by, allow_reviewer_admin=True)

    if registration.status not in {RegistrationStatus.REJECTED, RegistrationStatus.SUPPLEMENTED}:
        raise APIError(400, "Supplementary window can only be opened for correction-related statuses")
    existing = db.scalar(
        select(SupplementarySubmissionRecord).where(SupplementarySubmissionRecord.registration_form_id == registration.id)
    )
    if existing:
        raise APIError(400, "Supplementary submission already used")

    latest_trigger = db.scalar(
        select(ReviewWorkflowRecord)
        .where(
            ReviewWorkflowRecord.registration_form_id == registration.id,
            ReviewWorkflowRecord.to_status.in_([RegistrationStatus.SUPPLEMENTED, RegistrationStatus.REJECTED]),
        )
        .order_by(ReviewWorkflowRecord.created_at.desc())
        .limit(1)
    )
    trigger_time = latest_trigger.created_at if latest_trigger else registration.updated_at
    if datetime.now(timezone.utc) > trigger_time + timedelta(hours=72):
        raise APIError(400, "Supplementary submission window exceeded 72 hours")

    record = SupplementarySubmissionRecord(
        registration_form_id=registration.id,
        requested_by=requested_by.id,
        reason=reason,
        approved=True,
        opened_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc).replace(microsecond=0) + timedelta(hours=72),
        consumed=False,
    )
    registration.is_locked = False
    registration.status = RegistrationStatus.SUPPLEMENTED
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def get_registration_view(registration: RegistrationForm, viewer: User) -> dict:
    id_number = registration.id_number
    contact_phone = registration.contact_phone
    if viewer.role == UserRole.APPLICANT and viewer.id == registration.applicant_id:
        pass
    elif viewer.role == UserRole.SYSTEM_ADMIN:
        pass
    else:
        id_number = mask_id_number(id_number)
        contact_phone = mask_contact(contact_phone)

    return {
        "id": registration.id,
        "title": registration.title,
        "description": registration.description,
        "contact_phone": contact_phone,
        "id_number": id_number,
        "deadline_at": registration.deadline_at.isoformat() if registration.deadline_at else None,
        "status": registration.status.value,
        "is_locked": registration.is_locked,
    }
