from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Form
from app.core.dependencies import current_user
from app.services.soil_image import analyze
from app.core.database import get_db
from app.models.models import Farm, FertilizerRecommendation, PesticideRecommendation
from app.ml.fertilizer import recommend as fertilizer_recommend
from app.ml.pesticide import recommend as pesticide_recommend
from app.services.weather import get_weather

router = APIRouter(prefix="/soil", tags=["Soil"])


@router.post("/image-analysis")
async def image_analysis(file: UploadFile = File(...), user=Depends(current_user)):
    if file.content_type not in {"image/jpeg", "image/png", "image/webp"}:
        raise HTTPException(400, "Use JPG, PNG or WEBP")
    data = await file.read()
    if len(data) > 5 * 1024 * 1024:
        raise HTTPException(413, "Image is larger than 5 MB")
    return analyze(data)


def _soil_colour_from_analysis(result):
    r, g, b = result["average_rgb"]["r"], result["average_rgb"]["g"], result["average_rgb"]["b"]
    if result["brightness"] < 85:
        return "Black"
    if r > g * 1.12 and r > b * 1.18:
        return "Red" if result["brightness"] < 145 else "Laterite"
    if result["brightness"] > 185:
        return "Sandy"
    return "Loamy"


@router.post("/analyze-and-recommend")
async def analyze_and_recommend(
    file: UploadFile = File(...),
    crop: str = Form(...),
    crop_age_days: int = Form(0),
    farm_id: int | None = Form(None),
    user=Depends(current_user),
    db=Depends(get_db),
):
    if file.content_type not in {"image/jpeg", "image/png", "image/webp"}:
        raise HTTPException(400, "Use JPG, PNG or WEBP")
    data = await file.read()
    if len(data) > 5 * 1024 * 1024:
        raise HTTPException(413, "Image is larger than 5 MB")

    analysis = analyze(data)
    farm = None
    if farm_id:
        farm = db.query(Farm).filter(Farm.id == farm_id, Farm.farmer_id == user.id).first()
    if not farm:
        farm = db.query(Farm).filter(Farm.farmer_id == user.id).order_by(Farm.id).first()

    derived_colour = _soil_colour_from_analysis(analysis)
    payload = {
        "farm_id": farm.id if farm else None,
        "location": farm.location if farm else "Shivamogga",
        "crop": crop,
        "soil_type": (farm.soil_type if farm and farm.soil_type else derived_colour),
        "soil_color": derived_colour,
        "moisture": float(farm.moisture if farm and farm.moisture is not None else 55),
        "water_availability": float(farm.water_availability if farm and farm.water_availability is not None else 70),
        "previous_crop": farm.previous_crop if farm and farm.previous_crop else "Unknown",
        "previous_yield": float(farm.previous_yield if farm and farm.previous_yield is not None else 0),
    }
    recommendation = fertilizer_recommend(payload)
    rec = FertilizerRecommendation(
        farmer_id=user.id, farm_id=payload["farm_id"], crop=crop,
        preferred_fertilizer=None, predicted_fertilizer=recommendation["predicted_fertilizer"],
        suitability_score=recommendation["suitability_score"], model_used=recommendation["model_used"],
        explanation=recommendation["explanation"] + f" Soil image classification: {derived_colour}.",
    )
    db.add(rec)

    # Compute pesticide recommendation alongside soil test
    weather_data = get_weather(location=payload["location"])
    pest_payload = {
        "farm_id": payload["farm_id"],
        "location": payload["location"],
        "crop": crop,
        "crop_age_days": crop_age_days,
        "pest": "Soil-borne / Crop Pest",
        "temperature": weather_data.get("temperature", 28.0),
        "humidity": weather_data.get("humidity", 70.0),
        "rainfall": weather_data.get("rainfall", 0.0),
        "sunlight": weather_data.get("sunlight", 7.0),
        "observed_severity": 45.0,
    }
    pesticide_reco = pesticide_recommend(pest_payload)
    p_rec = PesticideRecommendation(
        farmer_id=user.id, farm_id=payload["farm_id"], crop=crop, pest="Soil-borne / Crop Pest",
        predicted_pesticide=pesticide_reco["predicted_pesticide"],
        pest_pressure_score=pesticide_reco["pest_pressure_score"],
        model_used=pesticide_reco["model_used"], explanation=pesticide_reco["explanation"],
    )
    db.add(p_rec)

    db.commit(); db.refresh(rec); db.refresh(p_rec)
    return {
        "soil_analysis": {**analysis, "derived_soil_color": derived_colour},
        **recommendation,
        "pesticide_recommendation": pesticide_reco,
        "recommendation_id": rec.id,
        "pesticide_recommendation_id": p_rec.id,
        "farm_id": payload["farm_id"],
        "crop_age_days": crop_age_days,
    }

