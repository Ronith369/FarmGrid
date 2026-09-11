from fastapi import APIRouter, Depends
from app.core.database import get_db
from app.core.dependencies import current_user
from app.models.models import FertilizerRecommendation, PesticideRecommendation
from app.schemas.common import FertilizerRequest, PesticideRequest
from app.ml.fertilizer import recommend as fertilizer_recommend
from app.ml.pesticide import recommend as pesticide_recommend

router = APIRouter(prefix="/ml", tags=["AI / ML"])


@router.post("/fertilizer/recommend")
def fertilizer(data: FertilizerRequest, db=Depends(get_db), user=Depends(current_user)):
    result = fertilizer_recommend(data.model_dump())
    db.add(FertilizerRecommendation(
        farmer_id=user.id,
        farm_id=data.farm_id,
        crop=data.crop,
        preferred_fertilizer=data.preferred_fertilizer,
        predicted_fertilizer=result["predicted_fertilizer"],
        suitability_score=result["suitability_score"],
        model_used=result["model_used"],
        explanation=result["explanation"],
    ))
    db.commit()
    return {**result, "preferred_fertilizer": data.preferred_fertilizer}


@router.post("/pesticide/recommend")
def pesticide(data: PesticideRequest, db=Depends(get_db), user=Depends(current_user)):
    result = pesticide_recommend(data.model_dump())
    db.add(PesticideRecommendation(
        farmer_id=user.id,
        farm_id=data.farm_id,
        crop=data.crop,
        pest=data.pest,
        predicted_pesticide=result["predicted_pesticide"],
        pest_pressure_score=result["pest_pressure_score"],
        model_used=result["model_used"],
        explanation=result["explanation"],
    ))
    db.commit()
    return result


@router.get("/fertilizer/history")
def fertilizer_history(db=Depends(get_db), user=Depends(current_user)):
    return db.query(FertilizerRecommendation).filter(
        FertilizerRecommendation.farmer_id == user.id
    ).order_by(FertilizerRecommendation.created_at.desc()).all()


@router.get("/pesticide/history")
def pesticide_history(db=Depends(get_db), user=Depends(current_user)):
    return db.query(PesticideRecommendation).filter(
        PesticideRecommendation.farmer_id == user.id
    ).order_by(PesticideRecommendation.created_at.desc()).all()
