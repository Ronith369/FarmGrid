# FarmGrid / ಕೃಷಿ ಮಿತ್ರ — Integrated Project

This package combines the supplied **ಕೃಷಿ ಮಿತ್ರ frontend** with the supplied **FarmGrid FastAPI backend**.

## What was integrated
- Existing farmer/provider HTML, CSS and dashboard UI retained.
- Login/session handling added using the backend JWT authentication.
- Farmer pages read farms, equipment, requests, labour providers and marketplace data from the API.
- Rental requests are persisted through `/api/requests` instead of only browser memory.
- Nutrition & Protection calls the backend fertilizer/pesticide recommendation APIs.
- Provider overview/equipment/labour/market pages read backend data.
- FastAPI serves the frontend at the same origin, so there is no `file://` CORS problem.
- Demo database seeding is included and remains persistent.
- Original React frontend from the backend package is preserved separately under `backend/frontend/` as a reference/API-connected implementation.

## Run (Windows)
1. Install Python 3.10+.
2. Double-click `backend/run_backend.bat` (or run it from a terminal).
3. Open **http://localhost:8000**.
4. Select Farmer or Provider and sign in.

The script creates a virtual environment, installs backend requirements, seeds missing demo data, and starts FastAPI.

## Demo accounts
- Farmer: `farmer@farmgrid.demo` / `farmgrid123`
- Provider: `owner@farmgrid.demo` / `farmgrid123`
- Admin: `admin@farmgrid.demo` / `farmgrid123`
- Buyer: `buyer@farmgrid.demo` / `farmgrid123`

## API
- Swagger UI: http://localhost:8000/docs
- Health: http://localhost:8000/api/health

## Notes
The fertilizer/pesticide models are demo decision-support models. Validate them with reliable region-specific agricultural data before real treatment decisions.


## Recent integration fixes
- Farmer equipment requests now create persistent provider notifications for the matching resource owner(s).
- Provider Overview and My Equipment use a provider-specific request inbox.
- Soil photo upload is connected to `/api/soil/analyze-and-recommend` and then the fertilizer recommender.
- Pesticide recommendations use the farm weather endpoint when farm coordinates are available.
- The official FarmGrid problem statement PDF is included at `docs/FarmGrid_Official_Problem_Statement.pdf`.
