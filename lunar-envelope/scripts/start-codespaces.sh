#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if python3 -c 'import socket; s=socket.socket(); s.settimeout(1); result=s.connect_ex(("127.0.0.1",8000)); s.close(); raise SystemExit(0 if result == 0 else 1)'; then
  echo 'Port 8000 is already in use. Check the Ports tab and /tmp/lunaris-codespaces.log.'
  exit 0
fi
nohup .venv/bin/python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 > /tmp/lunaris-codespaces.log 2>&1 < /dev/null &
echo 'Starting Lunaris. Open forwarded port 8000; logs: /tmp/lunaris-codespaces.log'
