#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
if [ ! -x backend/.venv/bin/python ]; then
  python3 -m venv backend/.venv
  backend/.venv/bin/pip install -r backend/requirements.txt
fi
backend/.venv/bin/python database/seed/seed_demo.py
backend/.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
