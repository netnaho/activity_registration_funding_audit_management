from datetime import datetime, timezone
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import APIError
from app.logging.logger import app_logger, log_info, log_warning
from app.models.enums import SeverityLevel, TransactionType
from app.models.funding_account import FundingAccount
from app.models.funding_transaction import FundingTransaction
from app.models.user import User
from app.services.metrics_service import create_alert
from app.storage.local_storage import LocalStorageService


logger = app_logger("app.finance")


def create_account(db: Session, *, account_name: str, category: str, period: str, budget_amount: float) -> FundingAccount:
    if budget_amount <= 0:
        raise APIError(400, "Budget amount must be positive")
    existing = db.scalar(select(FundingAccount).where(FundingAccount.account_name == account_name))
    if existing:
        raise APIError(400, "Funding account name already exists")
    account = FundingAccount(
        account_name=account_name,
        category=category,
        period=period,
        budget_amount=budget_amount,
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    log_info(
        logger,
        event="funding_account_created",
        category="business",
        context={"account_id": account.id, "account_name": account.account_name, "category": category, "period": period},
    )
    return account


def _account_expense_total(db: Session, account_id: int) -> float:
    total = db.scalar(
        select(func.coalesce(func.sum(FundingTransaction.amount), 0)).where(
            FundingTransaction.funding_account_id == account_id,
            FundingTransaction.transaction_type == TransactionType.EXPENSE,
        )
    )
    return float(total or 0)


def create_transaction(
    db: Session,
    *,
    account_id: int,
    transaction_type: TransactionType,
    amount: float,
    transaction_time: datetime,
    category: str,
    note: str | None,
    operator: User,
    invoice_file: UploadFile | None,
    overspend_confirmed: bool,
    storage: LocalStorageService,
) -> tuple[FundingTransaction, bool]:
    if amount <= 0:
        raise APIError(400, "Amount must be positive")

    account = db.scalar(select(FundingAccount).where(FundingAccount.id == account_id))
    if not account:
        raise APIError(404, "Funding account not found")

    projected_overspend = False
    if transaction_type == TransactionType.EXPENSE:
        current_expense = _account_expense_total(db, account_id)
        projected = current_expense + amount
        if projected > float(account.budget_amount) * 1.1:
            projected_overspend = True
            if not overspend_confirmed:
                log_warning(
                    logger,
                    event="overspend_confirmation_required",
                    category="business",
                    context={"account_id": account.id, "projected": projected, "budget": float(account.budget_amount)},
                )
                raise APIError(409, "Overspending warning: expenses exceed budget by 10%, confirmation required")
            create_alert(
                db,
                "overspending",
                SeverityLevel.WARNING,
                f"Account {account.account_name} exceeded budget threshold",
            )

    invoice_original_filename = None
    invoice_stored_filename = None
    invoice_sha256 = None
    if invoice_file is not None:
        payload = invoice_file.file.read()
        store_result = storage.save_bytes("invoices", invoice_file.filename or "invoice", payload)
        invoice_original_filename = invoice_file.filename
        invoice_stored_filename = str(store_result["stored_filename"])
        invoice_sha256 = str(store_result["sha256"])

    tx = FundingTransaction(
        funding_account_id=account_id,
        transaction_type=transaction_type,
        amount=amount,
        transaction_time=transaction_time,
        category=category,
        note=note,
        invoice_original_filename=invoice_original_filename,
        invoice_stored_filename=invoice_stored_filename,
        invoice_sha256=invoice_sha256,
        operator_id=operator.id,
        created_at=datetime.now(timezone.utc),
    )
    db.add(tx)
    db.commit()
    db.refresh(tx)
    log_info(
        logger,
        event="funding_transaction_recorded",
        category="business",
        context={"transaction_id": tx.id, "account_id": account.id, "transaction_type": tx.transaction_type.value, "overspend": projected_overspend},
    )
    return tx, projected_overspend


def finance_stats(db: Session, start_time: datetime | None, end_time: datetime | None) -> dict:
    query = select(FundingTransaction)
    if start_time:
        query = query.where(FundingTransaction.transaction_time >= start_time)
    if end_time:
        query = query.where(FundingTransaction.transaction_time <= end_time)
    txs = db.scalars(query).all()

    by_category: dict[str, float] = {}
    for tx in txs:
        by_category[tx.category] = by_category.get(tx.category, 0.0) + float(tx.amount)

    by_day: dict[str, float] = {}
    for tx in txs:
        day = tx.transaction_time.date().isoformat()
        by_day[day] = by_day.get(day, 0.0) + float(tx.amount)

    return {
        "total_transactions": len(txs),
        "by_category": by_category,
        "by_day": by_day,
    }
