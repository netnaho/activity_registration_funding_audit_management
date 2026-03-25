from datetime import datetime, timezone

import pytest

from app.core.exceptions import APIError
from app.models.enums import TransactionType, UserRole
from app.models.funding_account import FundingAccount
from app.services.finance_service import create_account, create_transaction
from app.storage.local_storage import LocalStorageService


class DummyUpload:
    filename = "invoice.pdf"
    content_type = "application/pdf"

    class _File:
        @staticmethod
        def read():
            return b"invoice-bytes"

    file = _File()


class DummyStorage(LocalStorageService):
    def __init__(self):
        pass

    def save_bytes(self, namespace: str, original_filename: str, payload: bytes):
        return {
            "stored_path": f"/{namespace}/x.pdf",
            "stored_filename": "x.pdf",
            "sha256": "abc123",
            "size_bytes": len(payload),
        }


def test_create_account_rejects_non_positive_budget(db_session):
    with pytest.raises(APIError) as exc:
        create_account(db_session, account_name="A", category="ops", period="p", budget_amount=0)
    assert exc.value.status_code == 400


def test_overspending_requires_confirmation(db_session, user_factory):
    operator = user_factory("finance_user_1", UserRole.FINANCIAL_ADMIN)
    account = create_account(db_session, account_name="Account O", category="ops", period="2026Q1", budget_amount=100)

    with pytest.raises(APIError) as exc:
        create_transaction(
            db=db_session,
            account_id=account.id,
            transaction_type=TransactionType.EXPENSE,
            amount=120,
            transaction_time=datetime.now(timezone.utc),
            category="ops",
            note="overspend",
            operator=operator,
            invoice_file=None,
            overspend_confirmed=False,
            storage=DummyStorage(),
        )
    assert exc.value.status_code == 409


def test_overspending_with_confirmation_succeeds(db_session, user_factory):
    operator = user_factory("finance_user_2", UserRole.FINANCIAL_ADMIN)
    account = create_account(db_session, account_name="Account C", category="ops", period="2026Q1", budget_amount=100)

    tx, warned = create_transaction(
        db=db_session,
        account_id=account.id,
        transaction_type=TransactionType.EXPENSE,
        amount=120,
        transaction_time=datetime.now(timezone.utc),
        category="ops",
        note="overspend confirmed",
        operator=operator,
        invoice_file=DummyUpload(),
        overspend_confirmed=True,
        storage=DummyStorage(),
    )
    assert tx.id is not None
    assert warned is True
