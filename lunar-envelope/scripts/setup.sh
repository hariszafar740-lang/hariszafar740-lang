#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
command -v python3 >/dev/null || { echo 'Python 3.11 or newer is required.' >&2; exit 1; }
command -v npm >/dev/null || { echo 'Node.js 20 or newer and npm are required.' >&2; exit 1; }
python3 -c 'import sys; assert sys.version_info >= (3,11), "Python 3.11 or newer is required"'
node -e 'if (+process.versions.node.split(".")[0] < 20) { console.error("Node.js 20 or newer is required"); process.exit(1); }'
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade 'pip>=26.2' 'setuptools>=84.1.0'
.venv/bin/python -m pip install -r backend/requirements.lock
(cd frontend && npm ci && npm run build)
