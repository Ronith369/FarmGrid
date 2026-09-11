from fastapi import APIRouter, Depends
from app.core.database import get_db
from app.core.dependencies import current_user
from app.models.models import Farm
from app.schemas.common import FarmCreate

router = APIRouter(prefix="/farms", tags=["Farms"])


@router.post("")
def create_farm(data: FarmCreate, db=Depends(get_db), user=Depends(current_user)):
    farm = Farm(farmer_id=user.id, **data.model_dump())
    db.add(farm)
    db.commit()
    db.refresh(farm)
    return farm


@router.get("")
def list_farms(db=Depends(get_db), user=Depends(current_user)):
    return db.query(Farm).filter(Farm.farmer_id == user.id).all()
