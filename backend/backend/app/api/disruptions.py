from fastapi import APIRouter, Depends, HTTPException
from app.core.database import get_db
from app.core.dependencies import role_required
from app.models.models import Disruption, Resource, Booking
from app.schemas.common import DisruptionCreate
from app.services.scheduler import feasible_slots
from app.services.notifications import create_notification

router = APIRouter(prefix="/disruptions", tags=["Disruptions"])


@router.post("")
def create(
    data: DisruptionCreate,
    db=Depends(get_db),
    user=Depends(role_required("resource_owner", "admin")),
):
    resource = db.query(Resource).filter(Resource.id == data.resource_id).first()
    if not resource:
        raise HTTPException(404, "Resource not found")

    disruption = Disruption(**data.model_dump())
    resource.status = "unavailable"
    resource.maintenance_status = "maintenance"
    db.add(disruption)
    db.commit()

    affected = db.query(Booking).filter(
        Booking.resource_id == resource.id,
        Booking.start_time >= data.start_time,
        Booking.status == "confirmed",
    ).all()

    alternatives = db.query(Resource).filter(
        Resource.id != resource.id,
        Resource.resource_type == resource.resource_type,
        Resource.status == "available",
        Resource.maintenance_status == "operational",
    ).all()

    plan = []
    for booking in affected:
        moved = False
        for alt in alternatives:
            existing = db.query(Booking).filter(
                Booking.resource_id == alt.id,
                Booking.status == "confirmed",
            ).all()
            slots = feasible_slots(
                booking.request.earliest_start,
                booking.request.latest_end,
                booking.request.duration_minutes,
                existing,
                30,
            )
            if slots:
                slot = slots[0]
                old = booking.resource_id
                booking.resource_id = alt.id
                booking.start_time = slot["start_time"]
                booking.end_time = slot["end_time"]
                booking.status = "reallocated"
                create_notification(
                    db,
                    booking.farmer_id,
                    "Schedule reallocated",
                    f"Your booking changed because of: {data.reason}",
                    "reallocation",
                )
                plan.append({
                    "booking_id": booking.id,
                    "old_resource_id": old,
                    "new_resource_id": alt.id,
                    "status": "reallocated",
                })
                moved = True
                break

        if not moved:
            plan.append({
                "booking_id": booking.id,
                "new_resource_id": None,
                "status": "needs_manual_action",
            })

    db.commit()
    return {"disruption_id": disruption.id, "affected": len(affected), "plan": plan}
