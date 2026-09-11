@echo off
cd /d %~dp0backend
if not exist .venv\Scripts\python.exe (
  python -m venv .venv
  call .venv\Scripts\activate
  python -m pip install --upgrade pip
  pip install -r requirements.txt
) else (
  call .venv\Scripts\activate
)
cd ..
python database\seed\seed_demo.py
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
