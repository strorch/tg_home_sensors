"""Initial tables.

Revision ID: 20260131_1400
Revises: 
Create Date: 2026-01-31 14:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "20260131_1400"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("chat_id", postgresql.BIGINT(), primary_key=True),
        sa.Column("humidity_min", postgresql.DOUBLE_PRECISION(), nullable=False, server_default="40.0"),
        sa.Column("humidity_max", postgresql.DOUBLE_PRECISION(), nullable=False, server_default="60.0"),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.Text(), nullable=False),
        sa.CheckConstraint("humidity_min >= 0.0 AND humidity_min <= 100.0"),
        sa.CheckConstraint("humidity_max >= 0.0 AND humidity_max <= 100.0"),
        sa.CheckConstraint("humidity_min < humidity_max"),
    )
    op.create_table(
        "alert_states",
        sa.Column(
            "chat_id",
            postgresql.BIGINT(),
            sa.ForeignKey("users.chat_id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("current_state", sa.Text(), nullable=False, server_default="normal"),
        sa.Column("last_alert_time", sa.Text()),
        sa.Column("last_alert_type", sa.Text()),
        sa.CheckConstraint("current_state IN ('normal', 'high_humidity', 'low_humidity')"),
        sa.CheckConstraint("last_alert_type IN ('high', 'low') OR last_alert_type IS NULL"),
    )


def downgrade() -> None:
    op.drop_table("alert_states")
    op.drop_table("users")
