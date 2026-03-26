from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.api.responses import success_response
from app.db.session import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.services.report_service import (
    export_audit_report,
    export_compliance_report,
    export_reconciliation_report,
    export_whitelist_policy_report,
)


router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.post("/reconciliation")
def reconciliation_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles({UserRole.FINANCIAL_ADMIN, UserRole.SYSTEM_ADMIN})),
):
    path = export_reconciliation_report(db, current_user)
    return success_response(data={"file_path": path}, msg="Reconciliation report exported")


@router.post("/audit")
def audit_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles({UserRole.SYSTEM_ADMIN, UserRole.REVIEWER})),
):
    path = export_audit_report(db, current_user)
    return success_response(data={"file_path": path}, msg="Audit report exported")


@router.post("/compliance")
def compliance_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles({UserRole.SYSTEM_ADMIN, UserRole.REVIEWER})),
):
    path = export_compliance_report(db, current_user)
    return success_response(data={"file_path": path}, msg="Compliance report exported")


@router.post("/whitelist")
def whitelist_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles({UserRole.SYSTEM_ADMIN})),
):
    path = export_whitelist_policy_report(db, current_user)
    return success_response(data={"file_path": path}, msg="Whitelist policy report exported")
