"""phase2 business tables and constraints

Revision ID: 0002_phase2_business
Revises: 0001_initial_schema
Create Date: 2026-03-24 00:30:00
"""

import sqlalchemy as sa
from alembic import op


revision = "0002_phase2_business"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    severity_level_enum = sa.Enum("info", "warning", "critical", name="severity_level_enum")

    op.create_table(
        "alert_records",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("alert_type", sa.String(length=64), nullable=False),
        sa.Column("severity", severity_level_enum, nullable=False),
        sa.Column("message", sa.String(length=512), nullable=False),
        sa.Column("is_resolved", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_alert_records_alert_type", "alert_records", ["alert_type"], unique=False)
    op.create_index("ix_alert_records_is_resolved", "alert_records", ["is_resolved"], unique=False)

    op.create_table(
        "report_exports",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("report_type", sa.String(length=64), nullable=False),
        sa.Column("file_path", sa.String(length=500), nullable=False),
        sa.Column("generated_by", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_report_exports_report_type", "report_exports", ["report_type"], unique=False)
    op.create_index("ix_report_exports_generated_by", "report_exports", ["generated_by"], unique=False)

    op.create_table(
        "collection_whitelist_policies",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("policy_name", sa.String(length=120), nullable=False, unique=True),
        sa.Column("scope_rule", sa.String(length=500), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.add_column("registration_forms", sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("registration_forms", sa.Column("is_locked", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column(
        "registration_material_submissions",
        sa.Column("is_locked", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_unique_constraint(
        "uq_registration_checklist_submission",
        "registration_material_submissions",
        ["registration_form_id", "checklist_item_id"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_registration_checklist_submission", "registration_material_submissions", type_="unique")
    op.drop_column("registration_material_submissions", "is_locked")
    op.drop_column("registration_forms", "is_locked")
    op.drop_column("registration_forms", "submitted_at")

    op.drop_table("collection_whitelist_policies")
    op.drop_index("ix_report_exports_generated_by", table_name="report_exports")
    op.drop_index("ix_report_exports_report_type", table_name="report_exports")
    op.drop_table("report_exports")

    op.drop_index("ix_alert_records_is_resolved", table_name="alert_records")
    op.drop_index("ix_alert_records_alert_type", table_name="alert_records")
    op.drop_table("alert_records")

    bind = op.get_bind()
    sa.Enum(name="severity_level_enum").drop(bind, checkfirst=True)
