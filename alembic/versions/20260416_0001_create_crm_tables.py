"""create crm tables

Revision ID: 20260416_0001
Revises:
Create Date: 2026-04-16 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260416_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "leads",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("owner_user_id", sa.Integer(), nullable=False),
        sa.Column("owner_chat_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("phone", sa.String(), nullable=True),
        sa.Column("telegram_user_id", sa.String(), nullable=True),
        sa.Column("telegram_username", sa.String(), nullable=True),
        sa.Column("telegram_display_name", sa.String(), nullable=True),
        sa.Column("lead_type", sa.String(), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("next_call_at", sa.String(), nullable=True),
        sa.Column("last_contact_at", sa.String(), nullable=True),
        sa.Column("capture_method", sa.String(), nullable=False),
        sa.Column("is_archived", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.String(), nullable=False),
        sa.Column("updated_at", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_leads_owner_archived",
        "leads",
        ["owner_user_id", "is_archived", "updated_at"],
        unique=False,
    )
    op.create_index("idx_leads_next_call", "leads", ["owner_user_id", "next_call_at"], unique=False)
    op.create_index(
        "idx_leads_telegram_user",
        "leads",
        ["owner_user_id", "telegram_user_id"],
        unique=False,
    )
    op.create_index(
        "idx_leads_telegram_username",
        "leads",
        ["owner_user_id", "telegram_username"],
        unique=False,
    )

    op.create_table(
        "lead_reminders",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("lead_id", sa.Integer(), nullable=False),
        sa.Column("scheduled_at", sa.String(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("sent_at", sa.String(), nullable=True),
        sa.Column("created_at", sa.String(), nullable=False),
        sa.Column("updated_at", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_active_reminder_per_lead",
        "lead_reminders",
        ["lead_id"],
        unique=True,
        sqlite_where=sa.text("is_active = 1"),
    )


def downgrade() -> None:
    op.drop_index("idx_active_reminder_per_lead", table_name="lead_reminders")
    op.drop_table("lead_reminders")
    op.drop_index("idx_leads_telegram_username", table_name="leads")
    op.drop_index("idx_leads_telegram_user", table_name="leads")
    op.drop_index("idx_leads_next_call", table_name="leads")
    op.drop_index("idx_leads_owner_archived", table_name="leads")
    op.drop_table("leads")
