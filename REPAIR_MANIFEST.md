# Phase 2 repair manifest

**Recorded:** 2026-10-11 (Asia/Karachi)

**Status:** PARTIALLY VERIFIED; see [AUDIT_REPORT.md](AUDIT_REPORT.md) for gates, numerical evidence, and unresolved risks.

## Scope and provenance

The six linked public repositories were copied from the audit-pinned snapshots below; their commit IDs were re-queried through the GitHub API and matched. Their repairs remain in local writable, non-Git copies under `/home/user/phase2-repairs/`; no commit, push, or PR was made for those six. The profile documentation edits from `profile-repository/` were committed to the primary checkout on `arena/5483384b-hariszafar740-lang` as `ca0c63bc3a2b5ccda044b4cbb4759ea6912360d7`, pushed to that branch, and proposed in [PR #1](https://github.com/hariszafar740-lang/hariszafar740-lang/pull/1) against `main`. The PR's `test-profile-docs` hosted check passed. The audit report and manifest are supporting documentation for that PR; the six external repair directories contain no `.git` metadata or remotes, so their content is not included in the PR.

| Repository | Audited baseline | Repair copy |
|---|---|---|
| `hariszafar740-lang` profile/docs | `796e92fdb323dd1a3bc23291992533e7a200d621` (local starting commit) | `profile-repository/` |
| `power-systems-newton-raphson-solver` | `e4624ed9cc5870d7da0fd2de6e71d6fb9fa72cb7` (`main`) | `power-systems-newton-raphson-solver/` |
| `solar-pv-mppt-dynamic-solver` | `270d22ab02b59be7478120c8ca8f12f9f784fbb1` (`feat/mppt-control-algorithms`) | `solar-pv-mppt-dynamic-solver/` |
| `bess-soc-dynamics-solver` | `0c4e9084cd20e8d545de4c4c7a41ca5cffc7f637` (`main`) | `bess-soc-dynamics-solver/` |
| `inverter-grid-control-solver` | `ca46d6c7f0fbceea47be5505ecd72bbf73e2b426` (`main`) | `inverter-grid-control-solver/` |
| `energy-transition-model` | `8e9e0e601b7d5e51493c814698733ef09bfa77d3` (`main`) | `energy-transition-model/` |
| `ee-portfolio-master` | `eacef5237bac90a79901b9a79ba691b4fb911ff3` (`main`) | `ee-portfolio-master/` |

No source files were deleted from the six external repair copies. Generated test/tool caches are not part of the source inventory.

## Exact changed-path inventory

### Profile documentation repository

- Modified: `README.md` (add the energy-transition project; correct capability language; document independent-model, data, certification, and test boundaries).
- Added: `requirements-dev.txt`, `tests/test_profile_readme.py`, `.github/workflows/docs-ci.yml`.

### Power-flow solver

- Modified: `README.md`, `main.py`, `src/bus_data.py`, `src/ieee14_data.py`, `src/jacobian_builder.py`, `src/line_flow_calculator.py`, `src/mismatch_calculator.py`, `src/nr_solver.py`, `src/visualizer.py`, `src/ybus_builder.py`, `tests/test_nr_solver.py`, `tests/test_ybus.py`.
- Added: `tests/test_jacobian.py`, `tests/test_line_flows.py`.
- Repair themes: canonical case14 branch charging/taps/bus shunt; matching complex-tap/shunt admittance and branch-flow equations; finite/type/input checks; returned-state residual history and a non-convergence guard; rounded reference, finite-difference Jacobian, and branch-balance regressions; accurate documentation.

### Solar PV/MPPT solver

- Added: `README.md`.
- Modified: `main.py`, `src/mppt_algorithms.py`, `src/pv_model.py`, `src/visualizer.py`, `tests/test_mppt.py`, `tests/test_pv_model.py`.
- Repair themes: bounded single-diode current solving; fit photocurrent/saturation current to stated STC `Isc`/`Voc`; reject invalid irradiance, temperature, and point counts; validate MPPT behavior on a stated profile; report the model maximum separately from incompatible nameplate MPP data. The nameplate calibration gap remains unresolved: no manufacturer/model identifier, datasheet URL, raw STC I-V points, or temperature coefficients are supplied; authoritative module data is required.

### BESS SoC/electro-thermal solver

- Added: `requirements.txt`.
- Modified: `README.md`, `main.py`, `src/bess_model.py`, `src/profile_generator.py`, `src/sensitivity_analysis.py`, `src/thermal_model.py`, `src/visualizer.py`, `tests/test_bess_model.py`, `tests/test_profile_generator.py`, `tests/test_sensitivity_analysis.py`, `tests/test_thermal_model.py`, `tests/test_visualizer.py`.
- Repair themes: immutable reference resistances; per-step Arrhenius scaling from reference values; exact RC and constant-input lumped thermal updates; validated seeds/inputs; cold-temperature regression; remove unsupported thermal-runaway wording and state units/model limitations.

### Inverter control solver

- Added: `README.md`, `requirements.txt`, `src/frt_controller.py`.
- Modified: `.github/workflows/ci.yml`, `main.py`, `src/benchmark.py`, `src/droop_control.py`, `src/power_measurement.py`, `src/virtual_impedance.py`, `src/virtual_inertia.py`, `src/visualizer.py`, `tests/test_compliance.py`, `tests/test_droop_control.py`, `tests/test_power_measurement.py`, `tests/test_virtual_impedance.py`, `tests/test_virtual_inertia.py`, `tests/test_visualizer.py`.
- Repair themes: consistent `dt`-based time samples; explicit current-limited sag-response scenario with reactive-current priority, recovery, and measurable P/Q changes; tests constrain behavior within the sag window; Python 3.11 workflow/dependencies; no standards-certification claim.

### Energy-transition model

- Added: `.github/workflows/ci.yml`, `requirements.txt`, `src/__init__.py`, `src/model.py`, `tests/test_model.py`.
- Modified: `.gitignore`, `README.md`, `main.py`.
- Repair themes: synthetic hourly solar/wind availability, custom/load profile validation, annual representative-day objective weighting, optimal-termination checks, annual dispatch/load summary, optimization regressions, and explicit generic-currency/illustrative-data limitations.

### Portfolio orchestrator

- Added: `portfolio_common.py`, `requirements.txt`, `tests/test_portfolio_automation.py`.
- Modified: `.github/dependabot.yml`, `.github/workflows/deploy_pages.yml`, `.github/workflows/portfolio_matrix_ci.yml`, `README.md`, `audit_portfolio.py`, `build_release.py`, `generate_architecture.py`, `generate_portfolio_report.py`, `portfolio_cli.py`, `profile_portfolio.py`, `setup_hooks.sh`, `update_portfolio_metadata.sh`.
- Repair themes: one local project manifest/path resolver; fail-closed `BLOCKED` states and subprocess exit propagation; isolated child `PYTHONPATH`; temporary profiler files; HTML escaping, clear badges, and no-overwrite reports; temporary archive plus atomic no-replace link and SHA-256; architecture-diagram idempotence and scope note; documented pinned workspace preconditions; narrow Bandit suppressions only for fixed `argv`/`shell=False` subprocess use. Live metadata and hook-install operations were not executed.

## Final local verification snapshot

- Test suites: **92 passed**, no failed/skipped tests (Power 11, PV 17, BESS 20, inverter 18, energy 10, portfolio 13, profile 3). The energy suite emits one third-party PyPSA/pandas 3.0 future-dtype warning.
- Portfolio CLI integration: **5/5 projects PASS; 76 child tests passed**. Portfolio Bandit/critical Flake8 audit: **5/5 PASS**. Profiling: **5/5 PASS**, profile data cleaned from temporary directories. HTML report generation and five-archive release creation: **PASS**.
- Default Ruff and critical Flake8: **PASS** in all seven repair copies. Limited Mypy 1.20.2 checks: **PASS** in all seven copies; this is not strict/full type coverage.
- Portfolio recursive Bandit scan: **38 low B101 test-assert findings only; zero medium/high**. Portfolio source scripts and all five child `src/` trees are clean; seven narrow `nosec` annotations cover the reviewed fixed-argv subprocess import/call warnings.
- A broader selected Ruff profile remains non-clean on line length (`E501`), explicit exception messages (`TRY003`), intentional test assertions (`S101`), and four shell-free fixed-argv calls (`S603`). All other selected rules pass when only those reviewed categories are excluded.
- Python 3.10 was **NOT RUN**. The profile documentation workflow passed on PR #1; other hosted workflows were **NOT RUN**. Hooks and live GitHub metadata writes were **NOT RUN**. The STC PV MPP/nameplate mismatch and all model-specific physical-validation limits remain open; see `AUDIT_REPORT.md`.
