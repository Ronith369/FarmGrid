from fastapi import APIRouter, Depends, HTTPException
from app.core.database import get_db
from app.core.dependencies import current_user
from app.models.models import LabourProvider, LabourRequest, LabourOffer
from app.schemas.common import LabourProviderCreate, LabourRequestCreate, LabourOfferCreate
from app.services.labour import match_providers, total_wage
from app.services.notifications import create_notification

router = APIRouter(prefix="/labour", tags=["Labour"])


@router.post("/providers")
def provider(data: LabourProviderCreate, db=Depends(get_db), user=Depends(current_user)):
    item = LabourProvider(user_id=user.id, **data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/providers")
def providers(region: str | None = None, db=Depends(get_db), user=Depends(current_user)):
    q = db.query(LabourProvider).filter(LabourProvider.is_active == True)
    if region:
        q = q.filter(LabourProvider.region.ilike(f"%{region}%"))
    return q.all()


@router.post("/requests")
def labour_request(data: LabourRequestCreate, db=Depends(get_db), user=Depends(current_user)):
    request = LabourRequest(farmer_id=user.id, **data.model_dump())
    db.add(request)
    db.commit()
    db.refresh(request)

    matches = []
    matched_providers = match_providers(db, request)
    for p in matched_providers:
        create_notification(
            db, p.user_id,
            "New labour request",
            f"{user.name} needs {request.work_type} for {request.workers_required} workers in {request.region}. "
            f"Start: {request.start_date:%d %b}. Duration: {request.duration_days} day(s).",
            "labour_request",
        )
        matches.append({
            "provider_id": p.id,
            "name": p.name,
            "provider_type": p.provider_type,
            "workers_available": p.workers_available,
            "wage_per_worker_day": p.daily_wage_per_worker,
            "estimated_total": total_wage(
                p.daily_wage_per_worker,
                request.workers_required,
                request.duration_days,
            ),
        })

    return {"request_id": request.id, "matches": matches}


@router.post("/offers")
def offer(data: LabourOfferCreate, db=Depends(get_db), user=Depends(current_user)):
    request = db.query(LabourRequest).filter(LabourRequest.id == data.labour_request_id).first()
    if not request:
        raise HTTPException(404, "Labour request not found")

    item = LabourOffer(**data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)

    return {
        "offer_id": item.id,
        "status": item.status,
        "estimated_total": total_wage(
            data.wage_per_worker_day,
            data.offered_workers,
            request.duration_days,
        ),
    }


@router.post("/offers/{offer_id}/accept")
def accept(offer_id: int, db=Depends(get_db), user=Depends(current_user)):
    item = db.query(LabourOffer).filter(LabourOffer.id == offer_id).first()
    if not item:
        raise HTTPException(404, "Offer not found")
    item.status = "accepted"
    request = db.query(LabourRequest).filter(LabourRequest.id == item.labour_request_id).first()
    if request:
        request.status = "matched"
    db.commit()
    return {"offer_id": item.id, "status": item.status}
