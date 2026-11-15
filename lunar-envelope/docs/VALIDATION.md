# Selected scientific checks and their limits

This document is an evidence map, not an independent expert review. Lunaris
is an exploratory prototype; do not use it for mission, power, communications,
equipment or EVA decisions.

## What is being compared

- **Geometry:** 120 selected Sun/Earth cases in
  `tests/horizons_broad_differences.csv`, derived from archived NASA/JPL
  Horizons inputs and compared with the application. The selected dates and
  sites are not a random or global sample. Horizons and the application use
  related lunar orientation models; this is a separate computational path,
  not an independent physical measurement.
- **Crossings:** eight selected comparisons in
  `tests/horizons_crossing_differences.csv`. The reference is a linear
  interpolation between Horizons samples, not an exact root. The analysis
  does not find crossings that the app missed.
- **Terrain:** the optional terrain screen is separate from the spherical
  site comparison. Resolution, raster edges, unobserved near-field and
  distant terrain, and sampling can affect it. See
  [terrain provenance](../data/terrain/README.md).

## Reproduce the summary

From `lunar-envelope`, after installing the project's dependencies, run:

    python scripts/summarize_validation.py
    python -m pytest -q tests/test_evidence_summary.py tests/test_geometry_upgrade.py

The first command reads the checked-in difference tables, calculates
selected-case maxima and fixture SHA-256 hashes. It does **not** query
Horizons or independently recompute the tables. The tests in
`test_geometry_upgrade.py` include recomputation against archived inputs and
selected tolerances; see that file and the
[ephemeris provenance](../data/ephemeris/README.md) for the full methodology,
source requests, scripts, tolerances and caveats. The tests are regression
checks, not global accuracy guarantees.

The additional tests check that increasing both clearances does not increase
midpoint overlap in one selected scenario and demonstrate a short synthetic
event that the 15-minute scan misses. Passing these checks does not establish
physical accuracy or prove all edge cases are handled.

## Important boundaries

- Site-comparison results use geometric target centers, a spherical Moon and
  a tangent-plane horizon; they omit terrain and antenna constraints. A
  numerical event bracket is not physical accuracy.
- Midpoint bins and the fixed event scan may miss short or grazing events.
  The +2° clearance comparison is a sensitivity example, not an uncertainty
  interval.
- A historical Diviner sample is not live telemetry or a model validation.
  The separate exosphere and dust models use illustrative assumptions.
- No independent human scientific review or mission suitability is claimed.
  More observations, uncertainty analysis and expert assessment are required.
