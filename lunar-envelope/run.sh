#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
command -v python3 >/dev/null || { echo 'Python 3 is required.' >&2; exit 1; }
command -v npm >/dev/null || { echo 'Node.js and npm are required.' >&2; exit 1; }
python3 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements.txt
(cd frontend && npm ci && npm run build)
echo 'Open http://127.0.0.1:8000 (Ctrl+C to stop)'
exec .venv/bin/python -m uvicorn backend.main:app --host 0.0.0.0 --port "${PORT:-8000}"
