# FarmGrid Demo Checklist

## Backend health
- `GET /api/health` → `{"status":"healthy"}`
- `GET /docs` → Swagger UI

## Core scheduling demo
- Farmer creates request
- Priority score is shown
- Allocation searches feasible resource slots
- Confirmation creates a booking
- Conflict service rejects overlapping bookings

## Dynamic disruption demo
- Resource owner creates a disruption
- Existing confirmed booking is checked
- Alternative resource is searched
- Booking can be reallocated and farmer receives a notification

## ML demo
- Fertilizer recommendation loads persisted model artifact
- Pest pressure/pesticide recommendation loads persisted model artifact
- No retraining is needed on app startup

## Data persistence
- Stop backend
- Start backend again
- Login and verify farms/requests/bookings still exist

## If something breaks
1. Confirm backend is running on port 8000.
2. Confirm frontend `VITE_API_URL` points to `http://localhost:8000/api`.
3. Re-run `python database/seed/seed_demo.py` only if demo data is missing.
4. Open `http://localhost:8000/docs` to test the exact endpoint independently of React.
