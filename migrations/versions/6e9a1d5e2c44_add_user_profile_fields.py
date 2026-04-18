"""add user profile fields

Revision ID: 6e9a1d5e2c44
Revises: 198ef165baca
Create Date: 2026-02-13 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "6e9a1d5e2c44"
down_revision: Union[str, Sequence[str], None] = "198ef165baca"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table("users"):
        op.create_table(
            "users",
            sa.Column("tg_id", sa.BigInteger(), primary_key=True),
            sa.Column("username", sa.String(length=255), nullable=True),
            sa.Column("first_name", sa.String(length=255), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("last_seen", sa.DateTime(timezone=True), nullable=True),
            sa.Column("is_subscribed", sa.Boolean(), nullable=True),
            sa.Column("subscription_expires_at", sa.DateTime(timezone=True), nullable=True),
        )
        op.create_index("ix_users_last_seen", "users", ["last_seen"], unique=False)
        return

    columns = {col["name"] for col in inspector.get_columns("users")}
    if "username" not in columns:
        op.add_column("users", sa.Column("username", sa.String(length=255), nullable=True))
    if "first_name" not in columns:
        op.add_column("users", sa.Column("first_name", sa.String(length=255), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table("users"):
        return

    columns = {col["name"] for col in inspector.get_columns("users")}
    if "first_name" in columns:
        op.drop_column("users", "first_name")
    if "username" in columns:
        op.drop_column("users", "username")

