# Lunaris — lunar environment lab

An exploratory mission-control prototype: interactive 3D Moon, selectable site, environmental sliders and hypothetical stress tests, a Python simulation API, and a CSV report. It is not a flight-qualified model, a forecast, or a basis for EVA decisions.

## Run on Kali Linux

Install Python 3, Python's venv module, Node.js (20 or newer) and npm first. From this folder:

```bash
./run.sh
```

Open http://127.0.0.1:8000. The script installs backend packages in `.venv`, installs the locked frontend dependencies, builds the frontend, and starts the single FastAPI server. Stop with Ctrl+C. Set `PORT=...` to choose a different port. The server binds all network interfaces, so use a firewall or change `--host` in `run.sh` if access should be local only. The build needs network access to PyPI and npm. Fonts have local fallbacks if Google Fonts is unreachable.

For development: start `python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000` from this folder using the venv; run `npm run dev` from `frontend` in a second terminal. Vite proxies `/api` to the backend. Run tests with `.venv/bin/pip install pytest httpx && .venv/bin/python -m pytest tests`; run `npm run build` in `frontend`. For browser smoke tests, start the application and run `CHROMIUM_PATH=/path/to/chromium npm run test:e2e` from `frontend`.

## What the model does

All inputs are bounded; the backend is deterministic. Longitude zero is the subsolar point at phase zero; the subsolar longitude travels 360° over a 29.53-day synodic cycle and latitude is fixed at zero. This simplified phase convention is not an ephemeris. No terrain or axial tilt is included. Temperature uses `T⁴ = 95⁴ + max(cos θ,0) (390⁴−95⁴)` K. A scalar current-balance proxy solves electron, ion, and photoelectron currents by bisection. Their amplitudes and characteristic energies are illustrative, not fitted. Neutral species use a simple isothermal barometric scale height `H=kT/(mg)` and illustrative surface abundances; it is not the full Chamberlain model and does not model sputtering or photoionization losses.

Dust concentration and deposition are empirical proxies for meteoroid flux and proximity to the terminator. A 1 μm grain charge and electric-force **magnitude** are compared with gravity plus an assumed cohesion, using an assumed 5 cm field length. This is not a directional loft solution, and the proxy dust concentration is not derived from that force comparison. The solar curve advances lunar phase in six-hour steps and integrates the illustrative deposition rate D in g/m²/day. Retention is `100 exp(-0.8 ∫D dt)` with assumed extinction coefficient 0.8 m²/g. Wind, UV and meteoroid inputs remain fixed during the projection. The risk strip and candidate intervals only screen the proxy thresholds and sunlight; they are not safe-EVA windows. Hazard categories are arbitrary screening thresholds, not validated risk or safe-EVA windows. Presets represent hypothetical slider combinations, not event reconstructions. The lunar texture, particle cloud and shell rings are schematic, not maps or 3D solver grids. Their visual appearance does not constitute a measurement.

## NASA data status

The project includes a **small historical LRO Diviner subset**: 551 binned brightness-temperature observations and the original PDS4 label, retrieved from a pinned GitHub mirror. The API validates the source-file checksums and schema and returns the nearest bin only within 2 km. Choose **GO TO SAMPLE SITE** to see one in the inspector and report. The sample is spatially sparse and records historical observing conditions; it is not a live feed, a global map, or a time-matched validation of the simulation. The model's temperature remains an independent grey-body proxy; no observation is used to calibrate it. NASA PDS could not be reached directly, so the mirror's claimed extraction has not been independently checked against the full NASA table. Product links, hashes, attribution, selection limitations, and provenance are in [data/diviner/README.md](data/diviner/README.md).

An optional generic utility accepts a *previously normalized* CSV with columns `timestamp,quantity,value,unit,source_url`: `.venv/bin/python backend/ingest.py /path/to/normalized.csv`. It checks basic formatting and a NASA/PDS-related URL domain; it is not a PDS parser and cannot verify provenance. Its output is not used by the Diviner endpoint or simulation. Full product ingestion, LADEE observations, broad Diviner coverage, and scientific calibration remain future work.

Physical context: [NASA Moon fact sheet](https://nssdc.gsfc.nasa.gov/planetary/factsheet/moonfact.html); [NASA LADEE mission](https://science.nasa.gov/mission/ladee/). Further model validation and independent scientific review are required.

## Phase 2 features and gaps

Guided Story Mode walks through the prototype. The inspector compares a nearby historic Diviner temperature against the grey-body model at approximately matching local solar time; season, terrain, and observation averaging are not matched, so it is **not validation**. The 30-day strip, CSV and PDF reports show illustrative screening results, not flight or EVA recommendations. No mitigation duty-cycle recommendation can be justified from these models. See [AUDIT.md](AUDIT.md) for the unfinished work and a self-audit; Phase 2 is **not complete**.

The product-specific ingestion tool can extract a bounded selection from the bundled sample or the original full, checksum-matched product (see the pinned URLs in `data/diviner/README.md`):

```bash
.venv/bin/python -m backend.diviner_ingest --table data/diviner/diviner_subset.tab --mode subset --output data/extract.csv --south -90 --north -88
```

It writes a separate provenance JSON and refuses an existing output; use `--mode full` for the original full table only. It cannot ingest LADEE or arbitrary PDS products. The row limit defaults to 10,000 and must be set explicitly up to 100,000. Extraction does not automatically add data to the app.

### Deployment

`docker build -t lunaris lunar-envelope` from the repository root and `docker run --rm -p 8000:8000 lunaris` run the frontend and API together. The container supports a `PORT` environment variable for platforms that assign one. This recipe is provided for deployment; it has not been deployed publicly. Use an HTTPS-capable hosting service, review security and resource limits, and do not expose the server directly without appropriate protection. GitHub Pages alone cannot run the Python API.

## API

- `GET /api/health` — readiness
- `POST /api/simulate` — accepts `phase`, `wind`, `uv`, `meteor`, `latitude`, `longitude`; returns model outputs and a 30-day curve.
- `GET /api/nasa-data` — reports availability and provenance of the bundled subset.
- `GET /api/diviner?latitude=...&longitude=...` — nearest historical bin only within 2 km.
- `POST /api/diviner-comparison` — approximate local-time comparison with caveats.
- `POST /api/export-report` and `POST /api/export-report.pdf` — CSV timeline or PDF summary.

## Audit and known gaps

Functional checks cover inputs, day/night behavior, bounded results, scenario response, CSV consistency, basic ingestion, frontend build and API availability. These tests do not validate the physical model. Phase 2 is incomplete: LADEE data, full-product verification, scientific validation and actual deployment remain outstanding. See `AUDIT.md`. Additional desired work includes labeled product parsers, actual mapped albedo/topography and Diviner temperatures, scientifically validated dust/plasma physics, browser compatibility and accessibility audits, and mission-risk validation. No claim of competition success or 10/10 quality is justified.
