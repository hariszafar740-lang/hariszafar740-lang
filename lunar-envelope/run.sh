#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
./scripts/setup.sh
port=${PORT:-8000}
host=${HOST:-127.0.0.1}
echo "Open http://127.0.0.1:${port} (Ctrl+C to stop)"
exec .venv/bin/python -m uvicorn backend.main:app --host "$host" --port "$port"
