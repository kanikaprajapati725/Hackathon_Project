#!/usr/bin/env bash
# 30% milestone: text-only triage. Creates the venv, seeds supported dataset cases, starts the server.
set -euo pipefail
cd "$(dirname "$0")"
if [ ! -d .venv ]; then
  python3 -m venv .venv && .venv/bin/pip install --upgrade pip && .venv/bin/pip install -r requirements.txt
fi
if [ ! -f data/careflow.db ]; then .venv/bin/python -m scripts.evaluate --seed; fi
echo "CareFlow AI (30%) on http://localhost:${PORT:-8001}  (login dr.mehta / demo)"
exec .venv/bin/uvicorn app.main:app --port "${PORT:-8001}"
