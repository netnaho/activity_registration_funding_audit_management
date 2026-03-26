from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from datetime import datetime, timedelta, timezone

from app.models.enums import RegistrationStatus, UserRole
from app.models.funding_account import FundingAccount
from app.models.material_checklist import MaterialChecklist, MaterialChecklistItem
from app.models.registration_form import RegistrationForm
from app.models.role_permission import RolePermission
from app.models.user import User


DEFAULT_PERMISSIONS = {
    UserRole.APPLICANT.value: ["registrations:write", "materials:write", "self:read"],
    UserRole.REVIEWER.value: ["registrations:read", "workflows:review", "audit:read"],
    UserRole.FINANCIAL_ADMIN.value: ["finance:write", "finance:read", "reports:read"],
    UserRole.SYSTEM_ADMIN.value: ["*"],
}


def seed_initial_data(db: Session) -> None:
    for role, permissions in DEFAULT_PERMISSIONS.items():
        for permission in permissions:
            exists = db.scalar(
                select(RolePermission).where(RolePermission.role == role, RolePermission.permission == permission)
            )
            if not exists:
                db.add(RolePermission(role=role, permission=permission))

    admin_user = db.scalar(select(User).where(User.username == settings.seed_admin_username))
    if not admin_user:
        db.add(
            User(
                username=settings.seed_admin_username,
                full_name=settings.seed_admin_full_name,
                password_hash=hash_password(settings.seed_admin_password),
                role=UserRole.SYSTEM_ADMIN,
                is_active=True,
            )
        )

    demo_accounts = [
        ("applicant", "Demo Applicant", UserRole.APPLICANT, "Applicant@123456"),
        ("reviewer", "Demo Reviewer", UserRole.REVIEWER, "Reviewer@123456"),
        ("finance", "Demo Finance", UserRole.FINANCIAL_ADMIN, "Finance@123456"),
    ]
    for username, full_name, role, password in demo_accounts:
        existing_user = db.scalar(select(User).where(User.username == username))
        if not existing_user:
            db.add(
                User(
                    username=username,
                    full_name=full_name,
                    password_hash=hash_password(password),
                    role=role,
                    is_active=True,
                )
            )

    checklist = db.scalar(select(MaterialChecklist).where(MaterialChecklist.name == "Default Registration Checklist"))
    if not checklist:
        checklist = MaterialChecklist(name="Default Registration Checklist", description="Default required materials", is_active=True)
        db.add(checklist)
        db.flush()

    required_items = [
        ("ACT_PLAN", "Activity Plan", True),
        ("BUDGET_PLAN", "Budget Plan", True),
        ("ID_DOC", "Identity Document", True),
    ]
    for code, name, required in required_items:
        exists_item = db.scalar(select(MaterialChecklistItem).where(MaterialChecklistItem.item_code == code))
        if not exists_item:
            db.add(
                MaterialChecklistItem(
                    checklist_id=checklist.id,
                    item_code=code,
                    item_name=name,
                    required=required,
                    max_size_mb=20,
                )
            )

    finance_account = db.scalar(select(FundingAccount).where(FundingAccount.account_name == "Default Activity Budget"))
    if not finance_account:
        db.add(
            FundingAccount(
                account_name="Default Activity Budget",
                category="operations",
                period="2026Q1",
                budget_amount=50000,
            )
        )

    db.commit()

    applicant = db.scalar(select(User).where(User.username == "applicant"))
    if applicant:
        sample_registration = db.scalar(
            select(RegistrationForm).where(
                RegistrationForm.applicant_id == applicant.id,
                RegistrationForm.title == "Sample Campus Activity",
            )
        )
        if not sample_registration:
            db.add(
                RegistrationForm(
                    applicant_id=applicant.id,
                    title="Sample Campus Activity",
                    description="Seeded registration for local verification",
                    contact_phone="1234567890",
                    id_number="ID123456789",
                    deadline_at=datetime.now(timezone.utc) + timedelta(days=10),
                    status=RegistrationStatus.DRAFT,
                )
            )
    db.commit()
