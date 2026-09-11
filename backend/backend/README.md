# FarmGrid Backend

FastAPI backend for the FarmGrid agricultural resource coordination demo.

## Run
```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python ../database/seed/seed_demo.py
uvicorn app.main:app --reload --port 8000
```

The SQLite database is persistent. Starting the API does **not** delete or recreate data. The ML demo models are already stored under `app/ml/artifacts/`; training is not required for each run.

API docs: http://localhost:8000/docs
