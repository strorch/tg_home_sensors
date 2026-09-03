"""Grafana dashboard regression tests."""

import json
from pathlib import Path
from typing import Any


def _dashboard() -> dict[str, Any]:
    path = Path("monitoring/grafana/dashboards/home-sensors.json")
    result: dict[str, Any] = json.loads(path.read_text())
    return result


def test_last_reading_age_ignores_uninitialized_timestamp() -> None:
    dashboard = _dashboard()
    panel = next(panel for panel in dashboard["panels"] if panel["id"] == 8)

    assert panel["targets"][0]["expr"] == (
        "(time() - home_sensor_last_reading_timestamp_seconds) "
        "and (home_sensor_last_reading_timestamp_seconds > 0)"
    )
