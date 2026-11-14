# Lunaris — presentation and submission preparation

This is a **draft**, not proof of challenge registration, submission, eligibility or an award. Adapt it to your actual team and work; do not claim unperformed validation. The official [2026 judging guide](https://www.spaceappschallenge.org/resources/judging-awards-guide/) requests either a video up to 30 seconds or slides with a 7-slide maximum (including title/introduction). Verify current event rules, deadlines, required external-resource attribution, and whether pre-event work is permitted with the organizers.

## 30-second demo narration

> Finding a lunar landing site isn't just a point on a map. It is a trade between sunlight and a view of Earth. Lunaris compares the two using NASA-derived lunar geometry. Move through time, adjust clearance assumptions, and pin one date against another. Here, adding two degrees changes the overlap dramatically. Export the reproducible inputs and results. This is a screening prototype: terrain and real communications constraints still need validation.

Show the site navigator, move the sky slider, pin the baseline, change a threshold, recalculate, and show the trade table. Narration timing varies; record and check that the final video is within the official limit. Do not call it live lunar telemetry.

## Seven-slide outline

1. **Lunaris:** Compare sunlight and Earth geometry for potential lunar sites. NASA Space Apps concept; not an official NASA product.
2. **The problem:** A potential landing site and date involve competing illumination and communications geometry. A spherical-horizon screen cannot establish an operational landing site.
3. **Our approach:** Up to three sites, selectable dates in 2026, target-center topocentric sky directions, Sun/Earth/overlap timelines, and configurable clearance thresholds. The slider shows the changing sky.
4. **Reproducible example:** Start 2026-11-14 12:00 UTC, 7 days, 60-minute bins, Sun and Earth thresholds 0°. Site A (-85°, 0°): 143 h overlap; Site B (-88°, -90°): 30 h overlap. At thresholds +2° for both, A: 98 h; B: 0 h. These are approximate bin-based geometric results, not site rankings or measured availability.
5. **Data and trust:** A checksum-checked 2020–2030 table calculated from pinned third-party copies of JPL DE421 / NAIF SPICE kernels, plus a third-party 2026 fallback; a sparse historical LRO Diviner subset; optional NASA DONKI CME context, off by default. See [dataset provenance](../data/ephemeris/README.md) and [Diviner provenance](../data/diviner/README.md). JSON includes the model version, data hash, assumptions and results.
6. **Limits and checks:** Spherical Moon; no LOLA terrain, shadows, antenna, operational constraints, or validated electrical power model. Selected geometry cases checked against CSPICE; test suite and desktop/mobile browser smoke tests are software checks, not independent scientific certification.
7. **Next steps:** Ingest and validate terrain horizons and broader data products; independent science and accessibility review; publish a monitored public demo. Cite all sources and licenses as required on the submission form.

## References for the project submission

- Challenge: https://www.spaceappschallenge.org/2026/challenges/lunar-landing-site-navigator/
- NASA NAIF: https://naif.jpl.nasa.gov/naif/data.html
- Pinned vector mirror and provenance: https://github.com/julianascencio/orbital-pv/tree/7c2b1a64f7d43b9662b022ac3b88351228bbd3cd/examples/lunar/_data
- Diviner source and mirror: see `data/diviner/README.md`.
- DONKI: https://ccmc.gsfc.nasa.gov/tools/DONKI/
- Software dependencies and licenses should also be reviewed and attributed; the list above is not a complete licensing audit.
