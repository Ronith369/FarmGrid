from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from app.core.database import get_db
from app.core.dependencies import current_user, role_required
from app.models.models import ResourceRequest, Resource, Booking
from app.services.scheduler import feasible_slots
from app.services.conflict import conflicts
from app.services.geo import distance_km, transit_minutes
from app.schemas.common import ResourceRequestCreate

router = APIRouter(prefix="/scheduling", tags=["Scheduling"])


@router.post("/allocate/{request_id}")
def allocate(
    request_id: int,
    db=Depends(get_db),
    user=Depends(role_required("farmer", "admin")),
):
    request = db.query(ResourceRequest).filter(ResourceRequest.id == request_id).first()
    if not request:
        raise HTTPException(404, "Request not found")
    if user.role == "farmer" and request.farmer_id != user.id:
        raise HTTPException(403, "Not your request")

    resources = db.query(Resource).filter(
        Resource.resource_type.ilike(request.resource_type),
        Resource.status == "available",
        Resource.maintenance_status == "operational",
    ).all()

    candidates = []
    for resource in resources:
        bookings = db.query(Booking).filter(
            Booking.resource_id == resource.id,
            Booking.status.in_(["confirmed", "pending", "reallocated"]),
        ).all()

        slots = feasible_slots(
            request.earliest_start,
            request.latest_end,
            request.duration_minutes,
            bookings,
            buffer_minutes=30,
        )

        for slot in slots:
            candidates.append({
                "resource_id": resource.id,
                "resource_name": resource.name,
                **slot,
            })

    return {"request_id": request.id, "feasible_slots": candidates}


@router.post("/confirm/{request_id}")
def confirm(
    request_id: int,
    resource_id: int,
    start_time: str,
    end_time: str,
    db=Depends(get_db),
    user=Depends(role_required("farmer", "admin")),
):
    request = db.query(ResourceRequest).filter(ResourceRequest.id == request_id).first()
    resource = db.query(Resource).filter(Resource.id == resource_id).first()

    if not request or not resource:
        raise HTTPException(404, "Request/resource not found")
    if user.role == "farmer" and request.farmer_id != user.id:
        raise HTTPException(403, "Not your request")

    start = datetime.fromisoformat(start_time)
    end = datetime.fromisoformat(end_time)

    existing = conflicts(db, Booking, resource_id, start, end)
    if existing:
        raise HTTPException(
            409,
            {"message": "Double booking prevented", "booking_ids": [b.id for b in existing]},
        )

    booking = Booking(
        request_id=request.id,
        resource_id=resource.id,
        farmer_id=request.farmer_id,
        start_time=start,
        end_time=end,
        buffer_minutes=30,
        status="confirmed",
    )
    request.status = "allocated"
    db.add(booking)
    db.commit()
    db.refresh(booking)

    return {"booking_id": booking.id, "status": booking.status}


@router.get("/calendar")
def calendar(db=Depends(get_db), user=Depends(current_user)):
    q = db.query(Booking)
    if user.role == "farmer":
        q = q.filter(Booking.farmer_id == user.id)
    return q.order_by(Booking.start_time).all()
