from fastapi import APIRouter
from app.api.auth import router as auth
from app.api.farms import router as farms
from app.api.resources import router as resources
from app.api.requests import router as requests
from app.api.scheduling import router as scheduling
from app.api.disruptions import router as disruptions
from app.api.weather import router as weather
from app.api.ml import router as ml
from app.api.soil import router as soil
from app.api.labour import router as labour
from app.api.market import router as market
from app.api.offline import router as offline
from app.api.dashboard import router as dashboard
from app.api.notifications import router as notifications

router = APIRouter()
for r in [
    auth, farms, resources, requests, scheduling, disruptions,
    weather, ml, soil, labour, market, offline, dashboard, notifications
]:
    router.include_router(r)
