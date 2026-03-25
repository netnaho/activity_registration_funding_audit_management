import csv
from datetime import datetime
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.audit_log import AuditLog
from app.models.collection_whitelist_policy import CollectionWhitelistPolicy
from app.models.funding_transaction import FundingTransaction
from app.models.registration_form import RegistrationForm
from app.models.report_export import ReportExport
from app.models.user import User


def _ensure_reports_dir() -> Path:
    path = Path(settings.reports_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _write_csv(path: Path, headers: list[str], rows: list[list[str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)


def export_reconciliation_report(db: Session, requester: User) -> str:
    txs = db.scalars(select(FundingTransaction).order_by(FundingTransaction.transaction_time.desc())).all()
    rows = [
        [
            str(tx.id),
            str(tx.funding_account_id),
            tx.transaction_type.value,
            str(tx.amount),
            tx.category,
            tx.transaction_time.isoformat(),
        ]
        for tx in txs
    ]
    path = _ensure_reports_dir() / f"reconciliation_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.csv"
    _write_csv(path, ["id", "account_id", "type", "amount", "category", "time"], rows)
    db.add(ReportExport(report_type="reconciliation", file_path=str(path), generated_by=requester.id))
    db.commit()
    return str(path)


def export_audit_report(db: Session, requester: User) -> str:
    logs = db.scalars(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(5000)).all()
    rows = [[str(log.id), str(log.actor_user_id or ""), log.action, log.target_type, log.target_id, log.created_at.isoformat()] for log in logs]
    path = _ensure_reports_dir() / f"audit_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.csv"
    _write_csv(path, ["id", "actor_user_id", "action", "target_type", "target_id", "created_at"], rows)
    db.add(ReportExport(report_type="audit", file_path=str(path), generated_by=requester.id))
    db.commit()
    return str(path)


def export_compliance_report(db: Session, requester: User) -> str:
    regs = db.scalars(select(RegistrationForm).order_by(RegistrationForm.created_at.desc())).all()
    rows = [[str(r.id), r.status.value, str(r.is_locked), r.created_at.isoformat()] for r in regs]
    path = _ensure_reports_dir() / f"compliance_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.csv"
    _write_csv(path, ["registration_id", "status", "is_locked", "created_at"], rows)
    db.add(ReportExport(report_type="compliance", file_path=str(path), generated_by=requester.id))
    db.commit()
    return str(path)


def export_whitelist_policy_report(db: Session, requester: User) -> str:
    policies = db.scalars(select(CollectionWhitelistPolicy).order_by(CollectionWhitelistPolicy.id.asc())).all()
    rows = [[str(p.id), p.policy_name, p.scope_rule, str(p.is_active)] for p in policies]
    path = _ensure_reports_dir() / f"whitelist_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.csv"
    _write_csv(path, ["id", "policy_name", "scope_rule", "is_active"], rows)
    db.add(ReportExport(report_type="whitelist", file_path=str(path), generated_by=requester.id))
    db.commit()
    return str(path)
