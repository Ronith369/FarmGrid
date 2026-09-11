from fastapi import APIRouter, Depends, HTTPException
from app.core.database import get_db
from app.core.dependencies import current_user
from app.models.models import LabourProvider, LabourRequest, LabourOffer
from app.schemas.common import LabourProviderCreate, LabourRequestCreate, LabourOfferCreate, LabourApproveRequest
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


@router.get("/requests")
def list_labour_requests(region: str | None = None, db=Depends(get_db), user=Depends(current_user)):
    q = db.query(LabourRequest)
    if user.role == "farmer":
        q = q.filter(LabourRequest.farmer_id == user.id)
    if region:
        q = q.filter(LabourRequest.region.ilike(f"%{region}%"))
    requests = q.order_by(LabourRequest.created_at.desc()).all()
    res = []
    for r in requests:
        res.append({
            "id": r.id,
            "farmer_id": r.farmer_id,
            "farmer_name": r.farmer.name if getattr(r, "farmer", None) else "Farmer",
            "work_type": r.work_type,
            "workers_required": r.workers_required,
            "start_date": r.start_date.isoformat() if r.start_date else None,
            "duration_days": r.duration_days,
            "region": r.region,
            "urgency": r.urgency,
            "status": r.status,
            "notes": getattr(r, "notes", None),
            "contractor_notes": getattr(r, "contractor_notes", None),
            "accepted_by_user_id": getattr(r, "accepted_by_user_id", None),
            "accepted_by_name": r.accepted_by.name if getattr(r, "accepted_by", None) else None,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        })
    return res


@router.post("/requests")
def labour_request(data: LabourRequestCreate, db=Depends(get_db), user=Depends(current_user)):
    request = LabourRequest(farmer_id=user.id, **data.model_dump())
    db.add(request)
    db.commit()
    db.refresh(request)

    matches = []
    matched_providers = match_providers(db, request)
    recipients = [p.user_id for p in matched_providers if p.user_id and p.user_id != user.id]
    if not recipients:
        from app.models.models import User
        recipients = [
            row[0] for row in db.query(User.id)
            .filter(User.role.in_(["resource_owner", "provider", "admin"]), User.id != user.id)
            .all()
        ]

    start_fmt = request.start_date.strftime("%d %b %Y") if request.start_date else "the specified day"
    for uid in set(recipients):
        create_notification(
            db, uid,
            "New Labour Requirement Posted",
            f"Farm Owner {user.name} needs {request.workers_required} workers for {request.work_type} on {start_fmt} in {request.region}.",
            "labour_request",
        )

    for p in matched_providers:
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

    return {"request_id": request.id, "matches": matches, "status": request.status}


@router.post("/offers")
def offer(data: LabourOfferCreate, db=Depends(get_db), user=Depends(current_user)):
    request = db.query(LabourRequest).filter(LabourRequest.id == data.labour_request_id).first()
    if not request:
        raise HTTPException(404, "Labour request not found")

    item = LabourOffer(**data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)

    create_notification(
        db, request.farmer_id,
        "Labour offer received!",
        f"{user.name} offered {item.offered_workers} workers for your {request.work_type} request at ₹{item.wage_per_worker_day}/day.",
        "labour_offer",
    )

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
        create_notification(
            db, request.farmer_id,
            "Labour crew confirmed!",
            f"Labour requirement #{request.id} for {request.work_type} has been matched & confirmed.",
            "labour_matched",
        )
    db.commit()
    return {"offer_id": item.id, "status": item.status}


@router.post("/requests/{request_id}/approve")
def approve_labour_request(
    request_id: int,
    payload: LabourApproveRequest | None = None,
    db=Depends(get_db),
    user=Depends(current_user),
):
    request = db.query(LabourRequest).filter(LabourRequest.id == request_id).first()
    if not request:
        raise HTTPException(404, "Labour request not found")

    request.status = "approved"
    request.accepted_by_user_id = user.id
    c_note = payload.contractor_notes if (payload and payload.contractor_notes) else f"Accepted by contractor {user.name}. Workers will be provided on the specified day."
    request.contractor_notes = c_note

    start_fmt = request.start_date.strftime("%d %b %Y") if request.start_date else "the specified day"
    create_notification(
        db, request.farmer_id,
        "Labour Request Accepted by Contractor!",
        f"Contractor {user.name} accepted your labour request for {request.work_type} ({request.workers_required} workers) on {start_fmt}. Workers will be provided on the specified day!",
        "labour_approved",
    )
    db.commit()
    return {"request_id": request.id, "status": request.status, "contractor_notes": request.contractor_notes}



