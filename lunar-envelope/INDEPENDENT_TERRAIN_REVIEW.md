# Independent terrain and horizon review — request not yet sent

**Status: no independent reviewer has been identified, contacted or accepted this phase.** This is a request template, not a review, endorsement or 10/10 score. Please identify an independent planetary topography, LOLA and illumination specialist and a contact method.

## Request to reviewer

Review `backend/terrain.py`, `backend/native_terrain.py`, `data/terrain/README.md`, `AUDIT.md`, the terrain tests, `scripts/validate_terrain_sources.py`, `scripts/compare_terrain_high_resolution.py`, and their archived results. Independently reproduce selected native-raster horizons and assess these questions:

1. Are the PDS products, registrations, scale, frame, azimuth/longitude, interpolation, seam/fallback, spherical geometry and observer-height assumptions implemented correctly?
2. Is the apparent agreement for the sampled cases appropriate, and what adversarial, geographically diverse or observational benchmarks are missing? In particular, examine 0–600 m terrain, steep local slopes, narrow features, 300 km cutoff, edge truncation, azimuth interpolation, time discretization, missing-data handling and unknown future leap seconds.
3. Are the sensitivity indicators clearly distinguished from a measured error bound or confidence interval? Are classifications and warnings appropriate for the scope and not likely to imply mission-safe visibility?
4. Specify reproducible findings, severity, acceptance criteria, corrections and tests. Independently check corrections and give a written follow-up acceptance or remaining objections. A score must be the reviewer's own, not the author's.

## Review record

- Reviewer, relevant expertise, affiliation, independence, conflicts and contact method: **not provided**
- Findings, evidence and acceptance criteria: **not received**
- Corrections and tests: **pending findings**
- Follow-up decision and date: **not received**

This is an exploratory model, not an operational visibility or safety tool. Source verification and selected numerical comparisons are not independent human review or evidence of global accuracy.
