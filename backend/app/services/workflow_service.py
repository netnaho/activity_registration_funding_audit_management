from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import APIError
from app.models.enums import RegistrationStatus
from app.models.registration_form import RegistrationForm
from app.models.review_workflow_record import ReviewWorkflowRecord
from app.models.user import User
from app.services.material_service import mark_latest_versions_needs_correction


ALLOWED_TRANSITIONS = {
    RegistrationStatus.SUBMITTED: {
        RegistrationStatus.APPROVED,
        RegistrationStatus.REJECTED,
        RegistrationStatus.CANCELED,
        RegistrationStatus.SUPPLEMENTED,
    },
    RegistrationStatus.SUPPLEMENTED: {
        RegistrationStatus.APPROVED,
        RegistrationStatus.REJECTED,
        RegistrationStatus.CANCELED,
        RegistrationStatus.PROMOTED_FROM_WAITLIST,
    },
    RegistrationStatus.REJECTED: {RegistrationStatus.PROMOTED_FROM_WAITLIST},
    RegistrationStatus.APPROVED: set(),
    RegistrationStatus.CANCELED: set(),
    RegistrationStatus.PROMOTED_FROM_WAITLIST: set(),
    RegistrationStatus.DRAFT: {RegistrationStatus.SUBMITTED},
}


def _validate_transition(from_status: RegistrationStatus, to_status: RegistrationStatus) -> None:
    allowed = ALLOWED_TRANSITIONS.get(from_status, set())
    if to_status not in allowed:
        raise APIError(400, f"Invalid workflow transition from {from_status.value} to {to_status.value}")


def apply_transition(
    db: Session,
    *,
    registration_id: int,
    target_status: RegistrationStatus,
    comment: str,
    reviewer: User,
    batch_ref: str | None = None,
) -> RegistrationForm:
    registration = db.scalar(select(RegistrationForm).where(RegistrationForm.id == registration_id))
    if not registration:
        raise APIError(404, "Registration not found")

    from_status = registration.status
    _validate_transition(from_status, target_status)

    if target_status in {RegistrationStatus.REJECTED, RegistrationStatus.SUPPLEMENTED, RegistrationStatus.CANCELED} and not comment:
        raise APIError(400, "Comment is required for this transition")

    registration.status = target_status
    if target_status == RegistrationStatus.SUPPLEMENTED:
        registration.is_locked = False
        db.flush()
        mark_latest_versions_needs_correction(db, registration.id)
    log = ReviewWorkflowRecord(
        registration_form_id=registration.id,
        reviewer_id=reviewer.id,
        from_status=from_status,
        to_status=target_status,
        comment=comment,
        batch_ref=batch_ref,
        created_at=datetime.now(timezone.utc),
    )
    db.add(log)
    db.commit()
    db.refresh(registration)
    return registration


def apply_batch_transition(
    db: Session,
    *,
    registration_ids: list[int],
    target_status: RegistrationStatus,
    comment: str,
    reviewer: User,
    batch_ref: str,
) -> list[int]:
    if len(registration_ids) > 50:
        raise APIError(400, "Batch review supports maximum 50 entries")
    updated: list[int] = []
    for rid in registration_ids:
        apply_transition(
            db,
            registration_id=rid,
            target_status=target_status,
            comment=comment,
            reviewer=reviewer,
            batch_ref=batch_ref,
        )
        updated.append(rid)
    return updated
