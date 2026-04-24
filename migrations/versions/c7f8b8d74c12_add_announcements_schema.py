"""add announcements schema

Revision ID: c7f8b8d74c12
Revises: 6e9a1d5e2c44
Create Date: 2026-04-24 06:20:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "c7f8b8d74c12"
down_revision: Union[str, Sequence[str], None] = "6e9a1d5e2c44"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("announcements"):
        op.create_table(
            "announcements",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("body_html", sa.Text(), nullable=False),
            sa.Column("body_plain", sa.Text(), nullable=True),
            sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("created_by_user_id", sa.BigInteger(), nullable=False),
            sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column(
                "state",
                sa.String(length=16),
                nullable=False,
                server_default="pending",
            ),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            "ix_announcements_scheduled_at",
            "announcements",
            ["scheduled_at"],
            unique=False,
        )
        op.create_index(
            "ix_announcements_state",
            "announcements",
            ["state"],
            unique=False,
        )
        return

    columns = {column["name"] for column in inspector.get_columns("announcements")}
    indexes = {index["name"] for index in inspector.get_indexes("announcements")}

    if "body_html" not in columns:
        op.add_column("announcements", sa.Column("body_html", sa.Text(), nullable=False))
    if "body_plain" not in columns:
        op.add_column("announcements", sa.Column("body_plain", sa.Text(), nullable=True))
    if "scheduled_at" not in columns:
        op.add_column("announcements", sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False))
    if "created_by_user_id" not in columns:
        op.add_column("announcements", sa.Column("created_by_user_id", sa.BigInteger(), nullable=False))
    if "sent_at" not in columns:
        op.add_column("announcements", sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True))
    if "state" not in columns:
        op.add_column(
            "announcements",
            sa.Column(
                "state",
                sa.String(length=16),
                nullable=False,
                server_default="pending",
            ),
        )
        op.execute(
            "UPDATE announcements SET state = CASE WHEN sent_at IS NULL THEN 'pending' ELSE 'sent' END"
        )
    if "error_message" not in columns:
        op.add_column("announcements", sa.Column("error_message", sa.Text(), nullable=True))
    if "created_at" not in columns:
        op.add_column("announcements", sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))

    if "ix_announcements_scheduled_at" not in indexes:
        op.create_index(
            "ix_announcements_scheduled_at",
            "announcements",
            ["scheduled_at"],
            unique=False,
        )
    if "ix_announcements_state" not in indexes:
        op.create_index(
            "ix_announcements_state",
            "announcements",
            ["state"],
            unique=False,
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table("announcements"):
        return

    indexes = {index["name"] for index in inspector.get_indexes("announcements")}
    if "ix_announcements_state" in indexes:
        op.drop_index("ix_announcements_state", table_name="announcements")
    if "ix_announcements_scheduled_at" in indexes:
        op.drop_index("ix_announcements_scheduled_at", table_name="announcements")
    op.drop_table("announcements")
