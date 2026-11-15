#!/usr/bin/env python3
"""Summarize archived comparisons; does not fetch new observations."""
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read_csv(path):
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def summarize():
    geometry_path = ROOT / "tests/horizons_broad_differences.csv"
    crossing_path = ROOT / "tests/horizons_crossing_differences.csv"
    geometry = read_csv(geometry_path)
    crossings = read_csv(crossing_path)

    if len(geometry) != 120 or len(crossings) != 8:
        raise ValueError("Unexpected fixture count; inspect input artifacts.")

    maxima = {}
    for body in ("SUN", "EARTH"):
        rows = [row for row in geometry if row["body"] == body]
        if len(rows) != 60:
            raise ValueError(f"Unexpected {body} fixture count")

        maxima[body.lower()] = {
            "cases": len(rows),
            "max_abs_elevation_deg": max(
                abs(float(row["delta_elevation_deg"])) for row in rows
            ),
            "max_abs_azimuth_deg": max(
                abs(float(row["delta_azimuth_deg"])) for row in rows
            ),
            "max_abs_distance_km": max(
                abs(float(row["delta_distance_km"])) for row in rows
            ),
        }

    return {
        "scope": (
            "Selected archived cases only; not global error bounds "
            "or independent human review."
        ),
        "geometry_cases": len(geometry),
        "within_2deg_reference_horizon": sum(
            abs(float(row["reference_elevation_deg"])) < 2
            for row in geometry
        ),
        "geometry_maxima": maxima,
        "crossing_cases": len(crossings),
        "max_abs_crossing_difference_s": max(
            abs(float(row["app_minus_horizons_s"])) for row in crossings
        ),
        "fixtures_sha256": {
            str(path.relative_to(ROOT)): hashlib.sha256(
                path.read_bytes()
            ).hexdigest()
            for path in (geometry_path, crossing_path)
        },
    }


if __name__ == "__main__":
    print(json.dumps(summarize(), indent=2, sort_keys=True))
