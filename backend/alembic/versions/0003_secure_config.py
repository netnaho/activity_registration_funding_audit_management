"""add secure config entries table

Revision ID: 0003_secure_config
Revises: 0002_phase2_business
Create Date: 2026-03-26 10:00:00
"""

import sqlalchemy as sa
from alembic import op


revision = "0003_secure_config"
down_revision = "0002_phase2_business"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "secure_config_entries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("config_key", sa.String(length=128), nullable=False, unique=True),
        sa.Column("encrypted_value", sa.String(length=4096), nullable=False),
        sa.Column("updated_by", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_secure_config_entries_config_key", "secure_config_entries", ["config_key"], unique=True)
    op.create_index("ix_secure_config_entries_updated_by", "secure_config_entries", ["updated_by"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_secure_config_entries_updated_by", table_name="secure_config_entries")
    op.drop_index("ix_secure_config_entries_config_key", table_name="secure_config_entries")
    op.drop_table("secure_config_entries")
