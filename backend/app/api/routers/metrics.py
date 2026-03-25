from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.api.responses import success_response
from app.core.config import settings
from app.db.session import get_db
from app.models.enums import SeverityLevel, UserRole
from app.models.user import User
from app.services.metrics_service import compute_and_store_metrics, create_alert


router = APIRouter(prefix="/api/metrics", tags=["metrics"])


@router.post("/recompute")
def recompute_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles({UserRole.SYSTEM_ADMIN, UserRole.REVIEWER})),
):
    metrics = compute_and_store_metrics(db)
    if metrics["approval_rate"] < settings.alert_approval_rate_min:
        create_alert(db, "approval_rate", SeverityLevel.WARNING, "Approval rate below threshold")
    if metrics["correction_rate"] > settings.alert_correction_rate_max:
        create_alert(db, "correction_rate", SeverityLevel.WARNING, "Correction rate above threshold")
    if metrics["overspending_rate"] > settings.alert_overspending_rate_max:
        create_alert(db, "overspending_rate", SeverityLevel.CRITICAL, "Overspending rate above threshold")
    return success_response(data=metrics, msg="Metrics recomputed")
