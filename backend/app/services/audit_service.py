from sqlalchemy.orm import Session

from app.logging.logger import app_logger, log_info
from app.logging.redaction import redact_mapping
from app.models.audit_log import AuditLog


logger = app_logger("app.audit")


def write_audit_log(
    db: Session,
    *,
    actor_user_id: int | None,
    action: str,
    target_type: str,
    target_id: str,
    details: str | None = None,
) -> None:
    safe_context = redact_mapping(
        {
            "actor_user_id": actor_user_id,
            "action": action,
            "target_type": target_type,
            "target_id": target_id,
            "details": details,
        }
    )
    log_info(logger, event="audit_event", category="business", context=safe_context)

    log = AuditLog(
        actor_user_id=actor_user_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=details,
    )
    db.add(log)
    db.commit()
