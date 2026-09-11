from fastapi import APIRouter, Depends
from app.core.database import get_db
from app.core.dependencies import current_user
from app.models.models import WeatherRecord
from app.services.weather import get_weather

router = APIRouter(prefix="/weather", tags=["Weather"])


@router.get("")
def weather(
    location: str = "Shivamogga",
    latitude: float | None = None,
    longitude: float | None = None,
    db=Depends(get_db),
    user=Depends(current_user),
):
    data = get_weather(latitude=latitude, longitude=longitude, location=location)
    record = WeatherRecord(
        location=location,
        latitude=latitude or 13.9299,
        longitude=longitude or 75.5681,
        **data,
    )
    db.add(record)
    db.commit()
    return {"location": location, "latitude": latitude, "longitude": longitude, **data}

