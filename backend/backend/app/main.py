from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.database import create_tables
from app.api.routes import router

app = FastAPI(
    title="FarmGrid API",
    version="1.0.0",
    description="Agricultural resource coordination and decision support backend",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin, "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")

@app.on_event("startup")
def startup():
    create_tables()

@app.get("/api/health")
def health():
    return {"status": "healthy", "service": "FarmGrid API"}

# Serve the supplied ಕೃಷಿ ಮಿತ್ರ HTML/CSS/JS frontend from the same FastAPI
# process. This removes CORS/file:// problems and gives the project one URL.
FRONTEND_DIR = Path(__file__).resolve().parents[3] / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
else:
    @app.get("/")
    def root():
        return {"name": "FarmGrid", "status": "running", "docs": "/docs"}
