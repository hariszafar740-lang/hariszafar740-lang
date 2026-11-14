# Lunaris — lunar environment lab

A Phase 1 exploratory mission-control prototype: interactive 3D Moon, selectable site, environmental sliders and hypothetical stress tests, a Python simulation API, and a CSV report. It is not a flight-qualified model, a forecast, or a basis for EVA decisions.

## Run on Kali Linux

Install Python 3, Python's venv module, Node.js (20 or newer) and npm first. From this folder:

```bash
./run.sh
```

Open http://127.0.0.1:8000. The script installs backend packages in `.venv`, installs the locked frontend dependencies, builds the frontend, and starts the single FastAPI server. Stop with Ctrl+C. Set `PORT=...` to choose a different port. The server binds all network interfaces, so use a firewall or change `--host` in `run.sh` if access should be local only. The build needs network access to PyPI and npm. Fonts have local fallbacks if Google Fonts is unreachable.

For development: start `python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000` from this folder using the venv; run `npm run dev` from `frontend` in a second terminal. Vite proxies `/api` to the backend. Run tests with `.venv/bin/pip install pytest httpx && .venv/bin/python -m pytest tests`; run `npm run build` in `frontend`.

## What the model does

All inputs are bounded; the backend is deterministic. Longitude zero is the subsolar point at phase zero; the subsolar longitude travels 360° over a 29.53-day synodic cycle and latitude is fixed at zero. This simplified phase convention is not an ephemeris. No terrain or axial tilt is included. Temperature uses `T⁴ = 95⁴ + max(cos θ,0) (390⁴−95⁴)` K. A scalar current-balance proxy solves electron, ion, and photoelectron currents by bisection. Their amplitudes and characteristic energies are illustrative, not fitted. Neutral species use a simple isothermal barometric scale height `H=kT/(mg)` and illustrative surface abundances; it is not the full Chamberlain model and does not model sputtering or photoionization losses.

Dust concentration and deposition are empirical proxies for meteoroid flux and proximity to the terminator. A 1 μm grain charge and electric-force **magnitude** are compared with gravity plus an assumed cohesion, using an assumed 5 cm field length. This is not a directional loft solution, and the proxy dust concentration is not derived from that force comparison. The solar curve uses `100 exp(-0.8 D t)` with illustrative extinction coefficient 0.8 m²/g and deposition D in g/m²/day. Hazard categories are arbitrary screening thresholds, not validated risk or safe-EVA windows. Presets represent hypothetical slider combinations, not event reconstructions. The lunar texture, particle cloud and shell rings are schematic, not maps or 3D solver grids. Their visual appearance does not constitute a measurement.

## NASA data status

The project includes a **small historical LRO Diviner subset**: 551 binned brightness-temperature observations and the original PDS4 label, retrieved from a pinned GitHub mirror. The API validates the source-file checksums and schema and returns the nearest bin only within 2 km. Choose **GO TO SAMPLE SITE** to see one in the inspector and report. The sample is spatially sparse and records historical observing conditions; it is not a live feed, a global map, or a time-matched validation of the simulation. The model's temperature remains an independent grey-body proxy; no observation is used to calibrate it. NASA PDS could not be reached directly, so the mirror's claimed extraction has not been independently checked against the full NASA table. Product links, hashes, attribution, selection limitations, and provenance are in [data/diviner/README.md](data/diviner/README.md).

An optional generic utility accepts a *previously normalized* CSV with columns `timestamp,quantity,value,unit,source_url`: `.venv/bin/python backend/ingest.py /path/to/normalized.csv`. It checks basic formatting and a NASA/PDS-related URL domain; it is not a PDS parser and cannot verify provenance. Its output is not used by the Diviner endpoint or simulation. Full product ingestion, LADEE observations, broad Diviner coverage, and scientific calibration remain future work.

Physical context: [NASA Moon fact sheet](https://nssdc.gsfc.nasa.gov/planetary/factsheet/moonfact.html); [NASA LADEE mission](https://science.nasa.gov/mission/ladee/). Further model validation and independent scientific review are required.

## API

- `GET /api/health` — readiness
- `POST /api/simulate` — accepts `phase`, `wind`, `uv`, `meteor`, `latitude`, `longitude`; returns model outputs and a 30-day curve.
- `GET /api/nasa-data` — reports availability and provenance of the bundled subset.
- `GET /api/diviner?latitude=...&longitude=...` — nearest historical bin only within 2 km.
- `POST /api/export-report` — same input, CSV snapshot and power curve.

## Audit and known gaps

Functional checks cover inputs, day/night behavior, bounded results, scenario response, CSV consistency, basic ingestion, frontend build and API availability. These tests do not validate the physical model. The Phase 1 prototype includes a representative historical Diviner subset, but its original full table could not be independently checked in this environment. Additional desired work includes labeled product parsers, actual mapped albedo/topography and Diviner temperatures, scientifically validated dust/plasma physics, browser compatibility and accessibility audits, and mission-risk validation. No claim of competition success or 10/10 quality is justified.
