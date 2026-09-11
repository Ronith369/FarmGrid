# FarmGrid — Complete Demo

This package is organized so you can run the hackathon demo without rebuilding the project from scratch every time.

## Included
- `backend/` — FastAPI APIs, scheduling, conflict prevention, weather, labour, marketplace, soil image analysis and ML services.
- `frontend/` — React + Vite dashboard connected to the backend.
- `database/` — persistent SQLite demo setup, schema reference and idempotent seed script.
- `docs/` — run and demo instructions.

## One-time setup
### 1. Backend
```bash
cd backend
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate
pip install -r requirements.txt
cd ..
python database/seed/seed_demo.py
```

### 2. Start API
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

### 3. Start frontend in another terminal
```bash
cd frontend
npm install
npm run dev
```
Open the Vite URL shown in the terminal, normally `http://localhost:5173`.

## Demo accounts
- Farmer: `farmer@farmgrid.demo` / `farmgrid123`
- Resource owner: `owner@farmgrid.demo` / `farmgrid123`
- Admin: `admin@farmgrid.demo` / `farmgrid123`
- Buyer: `buyer@farmgrid.demo` / `farmgrid123`

## Persistence
- The SQLite DB is stored at `backend/farmgrid.db`.
- API startup only calls `create_tables()`; it does not erase data.
- Demo ML model files live under `backend/app/ml/artifacts/` and are loaded directly. You do **not** need to retrain them each time.
- Run the seed script only when you want to create missing demo records. It is idempotent.

## Suggested demo flow
1. Login as Farmer.
2. Open My Farms and show soil/location inputs.
3. Create a tractor request with urgency/weather/crop-readiness scores.
4. Click Find & allocate to demonstrate feasible-slot scheduling and double-booking protection.
5. Open AI Recommendations and generate fertilizer/pest results.
6. Open Labour and show contractor/direct-worker options.
7. Open Yield Marketplace and respond to a buyer request.
8. Login as Resource Owner/Admin and show Master Control.

## Important
The fertilizer/pesticide outputs are demo decision-support models. They must be trained and validated on reliable region-specific agricultural data before being used for real farm treatment decisions.
