from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.alert_record import AlertRecord
from app.models.enums import RegistrationStatus, SeverityLevel, TransactionType
from app.models.funding_account import FundingAccount
from app.models.funding_transaction import FundingTransaction
from app.models.quality_validation_result import QualityValidationResult
from app.models.registration_form import RegistrationForm


def compute_and_store_metrics(db: Session) -> dict:
    total_reg = int(db.scalar(select(func.count(RegistrationForm.id))) or 0)
    approved = int(
        db.scalar(select(func.count(RegistrationForm.id)).where(RegistrationForm.status == RegistrationStatus.APPROVED)) or 0
    )
    corrected = int(
        db.scalar(select(func.count(RegistrationForm.id)).where(RegistrationForm.status == RegistrationStatus.SUPPLEMENTED)) or 0
    )

    approval_rate = (approved / total_reg) if total_reg else 0.0
    correction_rate = (corrected / total_reg) if total_reg else 0.0

    account_rows = db.execute(select(FundingAccount.id, FundingAccount.budget_amount)).all()
    overspent_accounts = 0
    for account_id, budget in account_rows:
        expense_total = db.scalar(
            select(func.coalesce(func.sum(FundingTransaction.amount), 0)).where(
                FundingTransaction.funding_account_id == account_id,
                FundingTransaction.transaction_type == TransactionType.EXPENSE,
            )
        )
        if float(expense_total or 0) > float(budget) * 1.1:
            overspent_accounts += 1
    overspending_rate = (overspent_accounts / len(account_rows)) if account_rows else 0.0

    some_registration_id = db.scalar(select(RegistrationForm.id).order_by(RegistrationForm.id).limit(1))
    if some_registration_id is None:
        return {
            "approval_rate": approval_rate,
            "correction_rate": correction_rate,
            "overspending_rate": overspending_rate,
        }

    metric = QualityValidationResult(
        registration_form_id=int(some_registration_id),
        approval_rate=approval_rate,
        correction_rate=correction_rate,
        overspending_rate=overspending_rate,
        created_at=datetime.now(timezone.utc),
    )
    db.add(metric)
    db.commit()

    return {
        "approval_rate": approval_rate,
        "correction_rate": correction_rate,
        "overspending_rate": overspending_rate,
    }


def create_alert(db: Session, alert_type: str, severity: SeverityLevel, message: str) -> None:
    db.add(AlertRecord(alert_type=alert_type, severity=severity, message=message, is_resolved=False))
    db.commit()
