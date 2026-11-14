# Lunaris: project audit and path to an exceptional submission

**Review date:** 2026-11-14. **Type:** engineering self-audit, not an independent domain-expert or external security audit. **Current overall judgment: 6/10 for a portfolio prototype**, not 6/10 for mission readiness. A numerical rating is subjective; it is not a contest ranking. Phase 2 is incomplete. No one can honestly guarantee a top-0.1% result, selection, or a win.

## Why this exists

Lunaris was built as a concept for a NASA Space Apps Challenge: to explore how NASA lunar observations and space-physics assumptions can inform a legible interface for hypothetical surface-power and operations questions. The goal is to make assumptions and uncertainties visible, not to claim a certified engineering product. This repository does not claim an official NASA affiliation, submission, judging result or endorsement. Check the current challenge's actual rules, judging criteria, eligibility, team requirements, data terms and deadlines before submitting.

## Evidence and scorecard

| Area | Assessment | Evidence / limitation |
| --- | --- | --- |
| Mission and presentation | **Promising prototype** | Purpose, source status, screenshot and 90-second path are documented; no public live demo or competition submission is established. |
| Science | **Major gap** | Charging, neutral-density, dust and PV models are simplified, uncalibrated proxies. Neither comparisons nor tests establish scientific validity. |
| NASA observations | **Partial** | 551 historical Diviner bins and their original PDS label are included from a pinned third-party mirror. SHA-256 and label schema are checked; the full NASA product was not independently accessible here. LADEE LDEX, UVS and NMS data are absent. |
| Operations | **Major gap** | The six-hour timeline and category thresholds are illustrative. No validated safe EVA window, duty cycle or hardware performance forecast is produced. |
| Experience and accessibility | **Partial** | Desktop and mobile Chromium smoke checks cover core interactions and exports. Numeric site inputs provide an alternative to pointer selection. No full keyboard, screen-reader, color-contrast, cross-browser or low-end-device audit. |
| Reliability and testing | **Partial** | 18 application tests, 10 root profile tests, a frontend production build and Chromium smoke tests were run in this environment; they cover selected cases, not all behavior or physics. A GitHub Actions workflow is included but its remote run must be checked after publication. |
| Security and dependency hygiene | **Initial checks only** | `npm audit` reported zero known findings for the installed lockfile; `pip-audit` reported none for the resolved Python runtime lock on this date. The original local venv contained old pip/setuptools advisories; setup now upgrades them. These point-in-time checks do not prove security, and dependencies must be re-audited regularly. |
| Recruiter access | **Improved, not solved** | Source is on a working branch, with a Codespaces configuration, screenshot, native instructions for three OS families, and a Docker recipe. Windows/macOS, Docker build and GitHub-hosted Codespaces were not tested here. A public HTTPS demo does not exist. |

## What the implementation actually does

- **Geometry and temperature:** a simplified 29.53-day phase rotates an equatorial subsolar longitude; no ephemeris, topography, axial tilt or shadows. A grey-body interpolation between fixed temperatures is not a Diviner map.
- **Plasma and gas:** scalar current-balance proxies have assumed currents and energies. The isothermal exponential density model uses illustrative surface abundances; a collisionless lunar exosphere is not fully described by this hydrostatic approximation. There is no full Chamberlain solver, ionization-loss model or validated solar-wind sputtering.
- **Dust and power:** electric force is compared by magnitude, not direction, with parameterized gravity and cohesion. Dust density and deposition are independent heuristic proxies; PV loss integrates an assumed exponential attenuation over 6-hour timesteps. No calibration, uncertainty intervals, terrain shielding, thermal drift or flight hardware validation exists.
- **Observations:** nearest Diviner bin is displayed only within 2 km. The local-time comparison does not match season, topography or historical averaging and must not be presented as validation. At other sites no reference is returned. There is no LADEE replay or claimed observation/model correlation.
- **Workflow:** presets are hypothetical combinations held constant over the projection. Screening windows are low-category sunlit model intervals, **not safe EVA windows**. Reports explicitly preserve that limitation. There are no validated mitigation recommendations.
- **3D:** the globe is a procedural texture and simplified lighting; rings and particles are schematic, not spatial grids. The app needs WebGL for the globe and currently has no fully tested no-WebGL fallback.

## Priority roadmap toward a competitive result

### P0 — trust, science, and access

1. **Obtain authentic data:** acquire representative LADEE LDEX, UVS and NMS products and corresponding PDS labels directly from NASA, retain product identifiers, checksums, timestamps, calibration flags, units and licensing; independently verify the Diviner sample against its full source. Build per-instrument label-aware, streaming ingestion with explicit quality flags, tests, and reproducible manifests. Never replace missing values with synthetic observations.
2. **Make comparison meaningful:** distinguish spatial and temporal sampling, instrument sensitivity and integration windows; match observation/model conditions; provide uncertainty, residuals and held-out events. Document where comparisons are invalid rather than forcing a curve fit. Validate independently with a planetary-science reviewer.
3. **Provide real easy access:** deploy the frontend and API together on a maintained HTTPS service with health checks, monitoring, usage limits, a privacy statement and a transparent data/status page. Confirm a public link from a logged-out browser and provide a no-install fallback walkthrough. GitHub Pages alone cannot serve the Python backend. Codespaces is a fallback, not a public live demo.
4. **Review engineering claims:** replace heuristic EVA language with clearly scoped decision support. Obtain domain review, define input limits and assumptions, document model uncertainty and sensitivity, and never suggest operational use until validated against relevant mission standards.

### P1 — scientific and technical depth

5. Implement a documented exosphere model appropriate for the collisionless regime, current balance and sheath physics with units and reference benchmarks, and dust charging/force direction/cohesion and deposition models with explicit parameter uncertainty. Use numerical convergence tests and independent published cases, not just tests of the same equations.
6. Introduce measured Diviner/LOLA terrain and temperature context, geographic coverage/no-data masks and realistic solar geometry. Separate absolute time, lunar phase, coordinate frame and uncertainty. Build deterministic event replays from actual archival observations; show true timestamps and coverage.
7. Add parameter sweeps and uncertainty propagation, e.g. calibrated ensembles or Monte Carlo with fixed seeds and confidence/credible intervals. Record model version, datasets, source hashes, parameters and assumptions in each export. Compare against a simple baseline before claiming improvement.
8. Add integration, property-based and regression tests, quantitative benchmark tolerances, static type checking/linting, test-coverage reporting, API contract tests and sustained multi-user load tests. Set measurable performance budgets using representative hardware and report median and p95, not a single best run.

### P2 — product polish and presentation

9. Complete WCAG-oriented keyboard, focus management, motion-reduction, color-contrast and screen-reader testing; add no-WebGL and slow-network fallbacks; test current Chrome, Firefox, Safari and mobile browsers. Provide text equivalents for charts and controls.
10. Harden deployment with authentication where appropriate, request-size and rate limits, security headers/CSP, dependency and container scanning, SBOM, non-root execution, pinned reproducible builds, secret-free CI and incident/maintenance plans. Audit licensing and third-party fonts/assets. Runtime version pins alone are not hash-verified reproducible builds.
11. Tell a concise story: who has the problem, how the data is used, what the model can and cannot answer, one reproducible scenario and its uncertainty, and what would be needed before real use. Create a short demo video and clear source/architecture diagrams. Obtain feedback from potential users and iterate with measurable tasks.

## Explicit verification boundaries

`lunar-envelope/README.md` contains repeatable commands and the data folder contains source links and hashes. Package scans and test results are snapshots, not future guarantees. GitHub Actions, Codespaces, Windows/macOS native workflows, Docker hosting and a public demo must each be tested separately in their target environment. This self-audit is not a substitute for independent scientific, security, accessibility or operations review.
