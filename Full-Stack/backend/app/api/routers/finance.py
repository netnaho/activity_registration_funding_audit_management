from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.api.responses import success_response
from app.db.session import get_db
from app.models.enums import TransactionType, UserRole
from app.models.funding_account import FundingAccount
from app.models.user import User
from app.schemas.finance import FundingAccountCreateRequest
from app.services.audit_service import write_audit_log
from app.services.finance_service import create_account, create_transaction, finance_stats
from app.storage.local_storage import LocalStorageService


router = APIRouter(prefix="/api/finance", tags=["finance"])


@router.get("/overview")
def finance_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles({UserRole.FINANCIAL_ADMIN, UserRole.SYSTEM_ADMIN})),
):
    accounts = db.scalars(select(FundingAccount).order_by(FundingAccount.id.desc())).all()
    return success_response(
        data={
            "accounts": [
                {
                    "id": a.id,
                    "account_name": a.account_name,
                    "category": a.category,
                    "period": a.period,
                    "budget_amount": float(a.budget_amount),
                }
                for a in accounts
            ]
        },
        msg="Finance overview",
    )


@router.post("/accounts")
def create_funding_account(
    payload: FundingAccountCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles({UserRole.FINANCIAL_ADMIN, UserRole.SYSTEM_ADMIN})),
):
    account = create_account(
        db,
        account_name=payload.account_name,
        category=payload.category,
        period=payload.period,
        budget_amount=payload.budget_amount,
    )
    write_audit_log(
        db,
        actor_user_id=current_user.id,
        action="funding_account_create",
        target_type="funding_account",
        target_id=str(account.id),
        details=account.account_name,
    )
    return success_response(
        data={
            "id": account.id,
            "account_name": account.account_name,
            "category": account.category,
            "period": account.period,
            "budget_amount": float(account.budget_amount),
        },
        msg="Funding account created",
    )


@router.post("/transactions")
def create_funding_transaction(
    funding_account_id: int = Form(...),
    transaction_type: str = Form(...),
    amount: float = Form(...),
    transaction_time: str = Form(...),
    category: str = Form(...),
    note: str | None = Form(default=None),
    overspend_confirmed: bool = Form(default=False),
    invoice_file: UploadFile | None = File(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles({UserRole.FINANCIAL_ADMIN, UserRole.SYSTEM_ADMIN})),
):
    storage = LocalStorageService()
    tx, overspend = create_transaction(
        db,
        account_id=funding_account_id,
        transaction_type=TransactionType(transaction_type),
        amount=amount,
        transaction_time=datetime.fromisoformat(transaction_time),
        category=category,
        note=note,
        operator=current_user,
        invoice_file=invoice_file,
        overspend_confirmed=overspend_confirmed,
        storage=storage,
    )
    write_audit_log(
        db,
        actor_user_id=current_user.id,
        action="funding_transaction_create",
        target_type="funding_transaction",
        target_id=str(tx.id),
        details=f"overspend={overspend}",
    )
    return success_response(
        data={
            "id": tx.id,
            "funding_account_id": tx.funding_account_id,
            "transaction_type": tx.transaction_type.value,
            "amount": float(tx.amount),
            "overspend_warning": overspend,
        },
        msg="Transaction recorded",
    )


@router.get("/stats")
def get_finance_stats(
    start_time: str | None = None,
    end_time: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles({UserRole.FINANCIAL_ADMIN, UserRole.SYSTEM_ADMIN})),
):
    start_dt = datetime.fromisoformat(start_time) if start_time else None
    end_dt = datetime.fromisoformat(end_time) if end_time else None
    return success_response(data=finance_stats(db, start_dt, end_dt), msg="Finance stats")
