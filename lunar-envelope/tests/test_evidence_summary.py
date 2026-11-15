"""Evidence and model behavior; not an independent science audit."""
import importlib.util
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from backend import events
from backend.planner import PlanRequest, compare

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "summarize_validation", ROOT / "scripts/summarize_validation.py"
)
summary_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(summary_module)


def test_selected_fixture_summary():
    summary = summary_module.summarize()
    assert summary["geometry_cases"] == 120
    assert summary["within_2deg_reference_horizon"] == 25
    assert summary["crossing_cases"] == 8
    assert summary["max_abs_crossing_difference_s"] < 30
    assert all(
        len(digest) == 64
        for digest in summary["fixtures_sha256"].values()
    )

    for body in ("sun", "earth"):
        maxima = summary["geometry_maxima"][body]
        assert maxima["cases"] == 60
        assert maxima["max_abs_elevation_deg"] < .001
        assert maxima["max_abs_azimuth_deg"] < .002


def test_stricter_midpoint_clearances_cannot_increase_overlap():
    base = {
        "start": "2026-11-14T12:00:00Z",
        "days": 1,
        "step_minutes": 60,
        "sites": [{"name": "A", "latitude": -85, "longitude": 0}],
    }

    low = compare(
        PlanRequest(**base, sun_clearance_deg=0, earth_clearance_deg=0)
    )["sites"][0]

    high = compare(
        PlanRequest(**base, sun_clearance_deg=2, earth_clearance_deg=2)
    )["sites"][0]

    assert high["sun_hours"] <= low["sun_hours"]
    assert high["earth_hours"] <= low["earth_hours"]
    assert high["overlap_hours"] <= low["overlap_hours"]
    assert high["overlap_hours"] == pytest.approx(
        low["overlap_hours_plus_2deg"]
    )


def test_fixed_scan_can_miss_short_excursion():
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)

    def brief(t):
        seconds = (t - start).total_seconds()
        return 1 if 300 < seconds < 360 else -1

    windows, transitions = events.threshold_windows(
        start,
        start + timedelta(minutes=30),
        timedelta(minutes=15),
        brief,
        0,
    )

    assert brief(start + timedelta(seconds=330)) > 0
    assert windows == []
    assert transitions == []
