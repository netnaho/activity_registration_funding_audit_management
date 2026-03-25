from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.api.responses import success_response
from app.core.exceptions import APIError
from app.db.session import get_db
from app.models.enums import RegistrationStatus, UserRole
from app.models.registration_form import RegistrationForm
from app.models.review_workflow_record import ReviewWorkflowRecord
from app.models.user import User
from app.schemas.workflow import BatchWorkflowTransitionRequest, WorkflowTransitionRequest
from app.services.audit_service import write_audit_log
from app.services.registration_service import assert_registration_actor_access
from app.services.workflow_service import apply_batch_transition, apply_transition


router = APIRouter(prefix="/api/workflows", tags=["workflows"])


@router.get("/queue")
def reviewer_queue(
    status: str | None = None,
    keyword: str | None = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles({UserRole.REVIEWER, UserRole.SYSTEM_ADMIN})),
):
    query = select(RegistrationForm)
    if status:
        query = query.where(RegistrationForm.status == status)
    if keyword:
        query = query.where(RegistrationForm.title.ilike(f"%{keyword}%"))
    rows = db.scalars(
        query.order_by(desc(RegistrationForm.created_at)).offset((page - 1) * page_size).limit(page_size)
    ).all()
    return success_response(
        data={
            "items": [
                {
                    "id": r.id,
                    "title": r.title,
                    "status": r.status.value,
                    "deadline_at": r.deadline_at.isoformat() if r.deadline_at else None,
                }
                for r in rows
            ],
            "page": page,
            "page_size": page_size,
        },
        msg="Reviewer queue",
    )


@router.post("/transition")
def transition(
    payload: WorkflowTransitionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles({UserRole.REVIEWER, UserRole.SYSTEM_ADMIN})),
):
    target = RegistrationStatus(payload.target_status)
    record = apply_transition(
        db,
        registration_id=payload.registration_id,
        target_status=target,
        comment=payload.comment,
        reviewer=current_user,
    )
    write_audit_log(
        db,
        actor_user_id=current_user.id,
        action="workflow_transition",
        target_type="registration",
        target_id=str(record.id),
        details=f"to {target.value}",
    )
    return success_response(data={"registration_id": record.id, "status": record.status.value}, msg="Transition applied")


@router.post("/batch-transition")
def batch_transition(
    payload: BatchWorkflowTransitionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles({UserRole.REVIEWER, UserRole.SYSTEM_ADMIN})),
):
    batch_ref = f"batch-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    updated = apply_batch_transition(
        db,
        registration_ids=payload.registration_ids,
        target_status=RegistrationStatus(payload.target_status),
        comment=payload.comment,
        reviewer=current_user,
        batch_ref=batch_ref,
    )
    write_audit_log(
        db,
        actor_user_id=current_user.id,
        action="workflow_batch_transition",
        target_type="workflow_batch",
        target_id=batch_ref,
        details=f"count={len(updated)} target={payload.target_status}",
    )
    return success_response(data={"updated_registration_ids": updated, "batch_ref": batch_ref}, msg="Batch transition applied")


@router.get("/{registration_id}/history")
def history(
    registration_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles({UserRole.REVIEWER, UserRole.SYSTEM_ADMIN, UserRole.APPLICANT})),
): 
    registration = db.scalar(select(RegistrationForm).where(RegistrationForm.id == registration_id))
    if not registration:
        raise APIError(404, "Registration not found")
    assert_registration_actor_access(registration=registration, actor=current_user, allow_reviewer_admin=True)

    logs = db.scalars(
        select(ReviewWorkflowRecord)
        .where(ReviewWorkflowRecord.registration_form_id == registration_id)
        .order_by(ReviewWorkflowRecord.created_at.asc())
    ).all()
    return success_response(
        data={
            "items": [
                {
                    "id": log.id,
                    "from_status": log.from_status.value,
                    "to_status": log.to_status.value,
                    "comment": log.comment,
                    "reviewer_id": log.reviewer_id,
                    "batch_ref": log.batch_ref,
                    "created_at": log.created_at.isoformat(),
                }
                for log in logs
            ]
        },
        msg="Workflow history",
    )
