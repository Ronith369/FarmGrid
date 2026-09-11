from fastapi import APIRouter, Depends
from app.core.database import get_db
from app.core.dependencies import role_required
from app.models.models import Resource, ResourceRequest, Booking, Disruption, LabourRequest, MarketOrder
from app.services.priority import priority

router = APIRouter(prefix="/dashboard", tags=["Master Dashboard"])


@router.get("/summary")
def summary(db=Depends(get_db), user=Depends(role_required("admin", "resource_owner"))):
    requests = db.query(ResourceRequest).all()
    scores = [priority(r)["total"] for r in requests]

    return {
        "resources": db.query(Resource).count(),
        "open_requests": db.query(ResourceRequest).filter(ResourceRequest.status == "pending").count(),
        "confirmed_bookings": db.query(Booking).filter(Booking.status == "confirmed").count(),
        "active_disruptions": db.query(Disruption).filter(Disruption.active == True).count(),
        "open_labour_requests": db.query(LabourRequest).filter(LabourRequest.status == "open").count(),
        "open_market_orders": db.query(MarketOrder).filter(MarketOrder.status == "open").count(),
        "average_priority": round(sum(scores) / len(scores), 2) if scores else 0,
    }


@router.get("/priority-queue")
def queue(db=Depends(get_db), user=Depends(role_required("admin", "resource_owner"))):
    requests = db.query(ResourceRequest).filter(ResourceRequest.status == "pending").all()
    result = [
        {"request_id": r.id, "farmer_id": r.farmer_id, "priority": priority(r)}
        for r in requests
    ]
    return sorted(result, key=lambda x: x["priority"]["total"], reverse=True)
