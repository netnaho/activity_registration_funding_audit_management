"""initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-03-24 00:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    user_role_enum = sa.Enum("applicant", "reviewer", "financial_admin", "system_admin", name="user_role_enum")
    registration_status_enum = sa.Enum(
        "draft",
        "submitted",
        "supplemented",
        "approved",
        "rejected",
        "canceled",
        "promoted_from_waitlist",
        name="registration_status_enum",
    )
    material_status_enum = sa.Enum("pending_submission", "submitted", "needs_correction", name="material_status_enum")
    transaction_type_enum = sa.Enum("income", "expense", name="transaction_type_enum")

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(length=64), nullable=False, unique=True),
        sa.Column("full_name", sa.String(length=128), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", user_role_enum, nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("failed_attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("first_failed_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_users_username", "users", ["username"], unique=True)
    op.create_index("ix_users_role", "users", ["role"], unique=False)

    op.create_table(
        "role_permissions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("permission", sa.String(length=128), nullable=False),
        sa.UniqueConstraint("role", "permission", name="uq_role_permission"),
    )
    op.create_index("ix_role_permissions_role", "role_permissions", ["role"], unique=False)
    op.create_index("ix_role_permissions_permission", "role_permissions", ["permission"], unique=False)

    op.create_table(
        "registration_forms",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("applicant_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("contact_phone", sa.String(length=32), nullable=False),
        sa.Column("id_number", sa.String(length=32), nullable=False),
        sa.Column("deadline_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", registration_status_enum, nullable=False, server_default="draft"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_registration_forms_applicant_id", "registration_forms", ["applicant_id"], unique=False)

    op.create_table(
        "material_checklists",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=150), nullable=False, unique=True),
        sa.Column("description", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "material_checklist_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("checklist_id", sa.Integer(), sa.ForeignKey("material_checklists.id", ondelete="CASCADE"), nullable=False),
        sa.Column("item_code", sa.String(length=64), nullable=False, unique=True),
        sa.Column("item_name", sa.String(length=150), nullable=False),
        sa.Column("required", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("max_size_mb", sa.Integer(), nullable=False, server_default="20"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "registration_material_submissions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "registration_form_id", sa.Integer(), sa.ForeignKey("registration_forms.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "checklist_item_id", sa.Integer(), sa.ForeignKey("material_checklist_items.id", ondelete="RESTRICT"), nullable=False
        ),
        sa.Column("total_size_bytes", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(
        "ix_registration_material_submissions_registration_form_id",
        "registration_material_submissions",
        ["registration_form_id"],
        unique=False,
    )

    op.create_table(
        "material_versions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "submission_id", sa.Integer(), sa.ForeignKey("registration_material_submissions.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("status", material_status_enum, nullable=False, server_default="pending_submission"),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("stored_filename", sa.String(length=255), nullable=False, unique=True),
        sa.Column("file_extension", sa.String(length=16), nullable=False),
        sa.Column("content_type", sa.String(length=128), nullable=False),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("sha256_hash", sa.String(length=64), nullable=False),
        sa.Column("uploaded_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("version_number >= 1 AND version_number <= 3", name="ck_material_versions_max_three"),
    )
    op.create_index("ix_material_versions_submission_id", "material_versions", ["submission_id"], unique=False)
    op.create_index("ix_material_versions_sha256_hash", "material_versions", ["sha256_hash"], unique=False)

    op.create_table(
        "review_workflow_records",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "registration_form_id", sa.Integer(), sa.ForeignKey("registration_forms.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("reviewer_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("from_status", registration_status_enum, nullable=False),
        sa.Column("to_status", registration_status_enum, nullable=False),
        sa.Column("comment", sa.Text(), nullable=False),
        sa.Column("batch_ref", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_review_workflow_records_registration_form_id", "review_workflow_records", ["registration_form_id"], unique=False)

    op.create_table(
        "funding_accounts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("account_name", sa.String(length=150), nullable=False, unique=True),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("period", sa.String(length=32), nullable=False),
        sa.Column("budget_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_funding_accounts_category", "funding_accounts", ["category"], unique=False)
    op.create_index("ix_funding_accounts_period", "funding_accounts", ["period"], unique=False)

    op.create_table(
        "funding_transactions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("funding_account_id", sa.Integer(), sa.ForeignKey("funding_accounts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("transaction_type", transaction_type_enum, nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("transaction_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("note", sa.String(length=500), nullable=True),
        sa.Column("invoice_original_filename", sa.String(length=255), nullable=True),
        sa.Column("invoice_stored_filename", sa.String(length=255), nullable=True),
        sa.Column("invoice_sha256", sa.String(length=64), nullable=True),
        sa.Column("operator_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_funding_transactions_funding_account_id", "funding_transactions", ["funding_account_id"], unique=False)
    op.create_index("ix_funding_transactions_transaction_type", "funding_transactions", ["transaction_type"], unique=False)
    op.create_index("ix_funding_transactions_transaction_time", "funding_transactions", ["transaction_time"], unique=False)

    op.create_table(
        "data_collection_batches",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("batch_code", sa.String(length=64), nullable=False, unique=True),
        sa.Column("description", sa.String(length=255), nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "quality_validation_results",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "registration_form_id", sa.Integer(), sa.ForeignKey("registration_forms.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("approval_rate", sa.Numeric(6, 3), nullable=False, server_default="0"),
        sa.Column("correction_rate", sa.Numeric(6, 3), nullable=False, server_default="0"),
        sa.Column("overspending_rate", sa.Numeric(6, 3), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(
        "ix_quality_validation_results_registration_form_id",
        "quality_validation_results",
        ["registration_form_id"],
        unique=False,
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("actor_user_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(length=128), nullable=False),
        sa.Column("target_type", sa.String(length=64), nullable=False),
        sa.Column("target_id", sa.String(length=64), nullable=False),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_audit_logs_actor_user_id", "audit_logs", ["actor_user_id"], unique=False)
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"], unique=False)
    op.create_index("ix_audit_logs_target_type", "audit_logs", ["target_type"], unique=False)
    op.create_index("ix_audit_logs_target_id", "audit_logs", ["target_id"], unique=False)
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"], unique=False)

    op.create_table(
        "login_attempt_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("success", sa.Boolean(), nullable=False),
        sa.Column("reason", sa.String(length=128), nullable=True),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.String(length=512), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_login_attempt_logs_username", "login_attempt_logs", ["username"], unique=False)
    op.create_index("ix_login_attempt_logs_user_id", "login_attempt_logs", ["user_id"], unique=False)
    op.create_index("ix_login_attempt_logs_success", "login_attempt_logs", ["success"], unique=False)
    op.create_index("ix_login_attempt_logs_created_at", "login_attempt_logs", ["created_at"], unique=False)

    op.create_table(
        "backup_records",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("backup_type", sa.String(length=32), nullable=False),
        sa.Column("file_path", sa.String(length=500), nullable=False),
        sa.Column("file_sha256", sa.String(length=64), nullable=False),
        sa.Column("file_size_bytes", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("triggered_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_backup_records_backup_type", "backup_records", ["backup_type"], unique=False)
    op.create_index("ix_backup_records_status", "backup_records", ["status"], unique=False)
    op.create_index("ix_backup_records_created_at", "backup_records", ["created_at"], unique=False)

    op.create_table(
        "supplementary_submission_records",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "registration_form_id", sa.Integer(), sa.ForeignKey("registration_forms.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("requested_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("reason", sa.String(length=500), nullable=False),
        sa.Column("approved", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_index(
        "ix_supplementary_submission_records_registration_form_id",
        "supplementary_submission_records",
        ["registration_form_id"],
        unique=False,
    )
    op.create_index(
        "ix_supplementary_submission_records_requested_by",
        "supplementary_submission_records",
        ["requested_by"],
        unique=False,
    )


def downgrade() -> None:
    for table_name in [
        "supplementary_submission_records",
        "backup_records",
        "login_attempt_logs",
        "audit_logs",
        "quality_validation_results",
        "data_collection_batches",
        "funding_transactions",
        "funding_accounts",
        "review_workflow_records",
        "material_versions",
        "registration_material_submissions",
        "material_checklist_items",
        "material_checklists",
        "registration_forms",
        "role_permissions",
        "users",
    ]:
        op.drop_table(table_name)

    bind = op.get_bind()
    sa.Enum(name="transaction_type_enum").drop(bind, checkfirst=True)
    sa.Enum(name="material_status_enum").drop(bind, checkfirst=True)
    sa.Enum(name="registration_status_enum").drop(bind, checkfirst=True)
    sa.Enum(name="user_role_enum").drop(bind, checkfirst=True)
