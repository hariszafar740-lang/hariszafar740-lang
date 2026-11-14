# Independent geometry review request — not yet sent

**Status: no independent expert has been identified, contacted or accepted this work.** This document is a request template, not a review or an endorsement. Step 1 remains incomplete pending external review and follow-up. Please identify an independent planetary-geometry/SPICE expert and a way to contact them.

## Request to reviewer

Please independently evaluate the 2020–2030 geometric lunar-site prototype and its evidence in `data/ephemeris/README.md`, `AUDIT.md`, `backend/ephemeris.py`, `backend/events.py`, `backend/planner.py`, and the scripts and fixtures cited there. It is a geometric spherical-Moon prototype, not a terrain horizon, flight or safety tool.

1. Check source-kernel provenance and the DE421 file discrepancy, frame transformation, lunar coordinate handedness and longitude convention, UTC/leap-second conversion, observer height and tangent-plane assumptions.
2. Independently reproduce or challenge the Horizons and CSPICE point and crossing comparisons; assess appropriateness of selected cases and tolerances. Suggest additional sites, dates, near-tangencies and negative cases, particularly events shorter than the fixed scan interval. Distinguish scientific uncertainty from numerical/regression tolerances.
3. Assess whether the interpolation, event detection, coverage, range, azimuth near zenith, and stated limitations are sufficiently accurate for the explicitly scoped prototype. Identify cases with incorrect or missing warnings or results.
4. Record each finding with severity, evidence, a reproducible case and acceptance criteria; explicitly state whether the scoped Step 1 is acceptable. A score is optional and must be the reviewer's own assessment, not the project author's.
5. Review the resulting corrections and tests and provide written follow-up acceptance or remaining objections.

## Evidence and unresolved limits

The selected comparisons are not global bounds or independent physical measurements; Horizons and the prototype use related JPL lunar-orientation conventions. Future leap seconds are unknown. The event scan can miss short/grazing crossings. No claim is made about terrain, actual visibility, operational use or mission certification. Check `data/ephemeris/README.md` for precise source URLs, conventions, data hashes and regeneration commands.

## Review record (to be completed by an independent human)

- Reviewer name, affiliation, relevant expertise, independence and conflicts: **not provided**
- Date and contact channel: **not provided**
- Findings and evidence: **not received**
- Corrections and reproducible tests: **pending findings**
- Follow-up acceptance or remaining objections: **not received**
