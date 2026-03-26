from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.api.responses import success_response
from app.core.exceptions import APIError
from app.models.enums import UserRole
from app.models.registration_form import RegistrationForm
from app.models.user import User
from app.schemas.registration import RegistrationCreateRequest, RegistrationSubmitRequest, SupplementaryRequest
from app.services.audit_service import write_audit_log
from app.services.registration_service import (
    assert_registration_actor_access,
    create_registration,
    create_supplementary_window,
    get_registration_view,
    maybe_lock_registration,
    submit_registration,
)
from app.db.session import get_db


router = APIRouter(prefix="/api/registrations", tags=["registrations"])


@router.get("")
def list_registrations(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles({UserRole.APPLICANT, UserRole.REVIEWER, UserRole.SYSTEM_ADMIN})),
):
    query = select(RegistrationForm)
    if current_user.role == UserRole.APPLICANT:
        query = query.where(RegistrationForm.applicant_id == current_user.id)
    records = db.scalars(query.order_by(RegistrationForm.created_at.desc())).all()

    payload = []
    changed = False
    for record in records:
        if maybe_lock_registration(record):
            changed = True
        payload.append(get_registration_view(record, current_user))
    if changed:
        db.commit()
    return success_response(data={"items": payload}, msg="Registration list")


@router.post("")
def create_registration_endpoint(
    payload: RegistrationCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles({UserRole.APPLICANT})),
):
    record = create_registration(
        db,
        applicant=current_user,
        title=payload.title,
        description=payload.description,
        contact_phone=payload.contact_phone,
        id_number=payload.id_number,
        deadline_at=payload.deadline_at,
    )
    write_audit_log(
        db,
        actor_user_id=current_user.id,
        action="registration_create",
        target_type="registration",
        target_id=str(record.id),
        details="Applicant created registration",
    )
    return success_response(data=get_registration_view(record, current_user), msg="Registration created")


@router.post("/submit")
def submit_registration_endpoint(
    payload: RegistrationSubmitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles({UserRole.APPLICANT})),
):
    record = submit_registration(db, payload.registration_id, current_user)
    write_audit_log(
        db,
        actor_user_id=current_user.id,
        action="registration_submit",
        target_type="registration",
        target_id=str(record.id),
        details="Applicant submitted registration",
    )
    return success_response(data=get_registration_view(record, current_user), msg="Registration submitted")


@router.post("/supplementary")
def create_supplementary_endpoint(
    payload: SupplementaryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles({UserRole.APPLICANT, UserRole.REVIEWER, UserRole.SYSTEM_ADMIN})),
):
    registration = db.scalar(select(RegistrationForm).where(RegistrationForm.id == payload.registration_id))
    if not registration:
        raise APIError(404, "Registration not found")

    assert_registration_actor_access(registration=registration, actor=current_user, allow_reviewer_admin=True)

    record = create_supplementary_window(db, registration, current_user, payload.reason)
    write_audit_log(
        db,
        actor_user_id=current_user.id,
        action="supplementary_open",
        target_type="registration",
        target_id=str(registration.id),
        details=payload.reason,
    )
    return success_response(
        data={
            "id": record.id,
            "registration_id": record.registration_form_id,
            "reason": record.reason,
            "expires_at": record.expires_at.isoformat(),
        },
        msg="Supplementary window opened",
    )
