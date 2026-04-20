"""announcement state and plain body

Revision ID: 20260421_0003
Revises: 20260420_0002
Create Date: 2026-04-21

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260421_0003"
down_revision: Union[str, None] = "20260420_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("announcements", sa.Column("body_plain", sa.Text(), nullable=True))
    op.add_column(
        "announcements",
        sa.Column("state", sa.String(length=16), server_default="pending", nullable=False),
    )
    op.add_column("announcements", sa.Column("error_message", sa.Text(), nullable=True))
    op.create_index("ix_announcements_state", "announcements", ["state"], unique=False)
    op.execute(
        "UPDATE announcements SET state = CASE WHEN sent_at IS NULL THEN 'pending' ELSE 'sent' END"
    )


def downgrade() -> None:
    op.drop_index("ix_announcements_state", table_name="announcements")
    op.drop_column("announcements", "error_message")
    op.drop_column("announcements", "state")
    op.drop_column("announcements", "body_plain")
