"""Add sensor readings history table.

Revision ID: 20260217_2100
Revises: 20260131_1400
Create Date: 2026-02-17 21:00:00.000000
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "20260217_2100"
down_revision = "20260131_1400"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("sensor_readings"):
        op.create_table(
            "sensor_readings",
            sa.Column("id", postgresql.BIGINT(), primary_key=True, autoincrement=True),
            sa.Column("recorded_at", sa.Text(), nullable=False),
            sa.Column("humidity", postgresql.DOUBLE_PRECISION(), nullable=False),
            sa.Column("dht_temperature", postgresql.DOUBLE_PRECISION(), nullable=False),
            sa.Column("lm35_temperature", postgresql.DOUBLE_PRECISION(), nullable=False),
            sa.Column("thermistor_temperature", postgresql.DOUBLE_PRECISION(), nullable=False),
        )
        inspector = sa.inspect(bind)

    indexes = {idx["name"] for idx in inspector.get_indexes("sensor_readings")}
    if "ix_sensor_readings_recorded_at" not in indexes:
        op.create_index(
            "ix_sensor_readings_recorded_at",
            "sensor_readings",
            ["recorded_at"],
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table("sensor_readings"):
        indexes = {idx["name"] for idx in inspector.get_indexes("sensor_readings")}
        if "ix_sensor_readings_recorded_at" in indexes:
            op.drop_index("ix_sensor_readings_recorded_at", table_name="sensor_readings")
        op.drop_table("sensor_readings")
