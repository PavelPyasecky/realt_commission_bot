"""rename subscription fields

Revision ID: 198ef165baca
Revises: 2a35001447f9
Create Date: 2026-02-05 01:47:55.360442

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '198ef165baca'
down_revision: Union[str, Sequence[str], None] = '2a35001447f9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column("users", "is_premium", new_column_name="is_subscribed")
    op.alter_column(
        "users",
        "premium_expires_at",
        new_column_name="subscription_expires_at",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column("users", "is_subscribed", new_column_name="is_premium")
    op.alter_column(
        "users",
        "subscription_expires_at",
        new_column_name="premium_expires_at",
    )
