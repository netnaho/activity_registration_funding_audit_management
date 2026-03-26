from fastapi import APIRouter, Depends
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.api.responses import success_response
from app.core.exceptions import APIError
from app.db.session import get_db
from app.models.alert_record import AlertRecord
from app.models.enums import UserRole
from app.models.user import User


router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.get("")
def list_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles({UserRole.SYSTEM_ADMIN, UserRole.FINANCIAL_ADMIN, UserRole.REVIEWER})),
):
    records = db.scalars(select(AlertRecord).order_by(desc(AlertRecord.created_at)).limit(200)).all()
    return success_response(
        data={
            "items": [
                {
                    "id": a.id,
                    "alert_type": a.alert_type,
                    "severity": a.severity.value,
                    "message": a.message,
                    "is_resolved": a.is_resolved,
                    "created_at": a.created_at.isoformat(),
                }
                for a in records
            ]
        },
        msg="Alerts",
    )


@router.post("/{alert_id}/resolve")
def resolve_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles({UserRole.SYSTEM_ADMIN})),
):
    alert = db.scalar(select(AlertRecord).where(AlertRecord.id == alert_id))
    if not alert:
        raise APIError(404, "Alert not found")
    alert.is_resolved = True
    db.commit()
    return success_response(data={"id": alert.id, "is_resolved": True}, msg="Alert resolved")
