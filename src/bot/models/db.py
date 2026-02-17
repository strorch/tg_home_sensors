"""SQLAlchemy table metadata."""

from sqlalchemy import CheckConstraint, Column, ForeignKey, Index, MetaData, Table, Text
from sqlalchemy.dialects.postgresql import BIGINT, DOUBLE_PRECISION


metadata = MetaData()

users = Table(
    "users",
    metadata,
    Column("chat_id", BIGINT, primary_key=True),
    Column("humidity_min", DOUBLE_PRECISION, nullable=False, server_default="40.0"),
    Column("humidity_max", DOUBLE_PRECISION, nullable=False, server_default="60.0"),
    Column("created_at", Text, nullable=False),
    Column("updated_at", Text, nullable=False),
    CheckConstraint("humidity_min >= 0.0 AND humidity_min <= 100.0"),
    CheckConstraint("humidity_max >= 0.0 AND humidity_max <= 100.0"),
    CheckConstraint("humidity_min < humidity_max"),
)

alert_states = Table(
    "alert_states",
    metadata,
    Column("chat_id", BIGINT, ForeignKey("users.chat_id", ondelete="CASCADE"), primary_key=True),
    Column("current_state", Text, nullable=False, server_default="normal"),
    Column("last_alert_time", Text),
    Column("last_alert_type", Text),
    CheckConstraint("current_state IN ('normal', 'high_humidity', 'low_humidity')"),
    CheckConstraint("last_alert_type IN ('high', 'low') OR last_alert_type IS NULL"),
)

sensor_readings = Table(
    "sensor_readings",
    metadata,
    Column("id", BIGINT, primary_key=True, autoincrement=True),
    Column("recorded_at", Text, nullable=False),
    Column("humidity", DOUBLE_PRECISION, nullable=False),
    Column("dht_temperature", DOUBLE_PRECISION, nullable=False),
    Column("lm35_temperature", DOUBLE_PRECISION, nullable=False),
    Column("thermistor_temperature", DOUBLE_PRECISION, nullable=False),
)

Index("ix_sensor_readings_recorded_at", sensor_readings.c.recorded_at)
