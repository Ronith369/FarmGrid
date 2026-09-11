from fastapi import APIRouter, Depends, HTTPException
from app.core.database import get_db
from app.core.dependencies import current_user, role_required
from app.models.models import ResourceRequest, Resource, User
from app.services.notifications import create_notification
from app.schemas.common import ResourceRequestCreate
from app.services.priority import priority

router = APIRouter(prefix="/requests", tags=["Resource Requests"])


@router.post("")
def create_request(
    data: ResourceRequestCreate,
    db=Depends(get_db),
    user=Depends(role_required("farmer", "admin")),
):
    request = ResourceRequest(farmer_id=user.id, **data.model_dump())
    db.add(request)
    db.commit()
    db.refresh(request)

    # Notify the provider(s) who can actually fulfil this request.
    resource = None
    recipients = []
    if request.requested_resource_id:
        resource = db.query(Resource).filter(Resource.id == request.requested_resource_id).first()
        if resource and resource.owner_id != user.id:
            recipients = [resource.owner_id]
    else:
        recipients = [
            row[0] for row in db.query(Resource.owner_id)
            .filter(Resource.resource_type.ilike(request.resource_type),
                    Resource.owner_id != user.id)
            .distinct().all()
        ]

    # If no specific resource owner matched, notify all providers/resource owners
    if not recipients:
        recipients = [
            row[0] for row in db.query(User.id)
            .filter(User.role.in_(["resource_owner", "provider", "admin"]), User.id != user.id)
            .all()
        ]

    score = priority(request)
    resource_label = resource.name if resource else request.resource_type.title()
    for provider_id in recipients:
        create_notification(
            db, provider_id,
            "New farmer resource request",
            f"{user.name} requested {resource_label} for {request.crop} ({request.crop_stage}). "
            f"Window: {request.earliest_start:%d %b %H:%M}–{request.latest_end:%d %b %H:%M}. "
            f"Priority: {score['total']}/100.",
            "resource_request",
        )

    return {"id": request.id, "status": request.status, "priority": score, "notified_providers": len(recipients)}


@router.get("")
def list_requests(
    status: str | None = None,
    db=Depends(get_db),
    user=Depends(current_user),
):
    q = db.query(ResourceRequest)
    if user.role == "farmer":
        q = q.filter(ResourceRequest.farmer_id == user.id)
    if status:
        q = q.filter(ResourceRequest.status == status)

    result = []
    for r in q.order_by(ResourceRequest.created_at.desc()).all():
        result.append({
            "id": r.id,
            "farmer_id": r.farmer_id,
            "farmer_name": r.farmer.name if r.farmer else "Farmer",
            "requested_resource_id": r.requested_resource_id,
            "resource_type": r.resource_type,
            "crop": r.crop,
            "crop_stage": r.crop_stage,
            "earliest_start": r.earliest_start,
            "latest_end": r.latest_end,
            "duration_minutes": r.duration_minutes,
            "created_at": r.created_at,
            "status": r.status,
            "priority": priority(r),
        })
    return result


@router.get("/provider/inbox")
def provider_inbox(db=Depends(get_db), user=Depends(role_required("resource_owner", "provider", "admin"))):
    """Requests relevant to this provider's equipment, or all pending requests if general provider."""
    resources = db.query(Resource).filter(Resource.owner_id == user.id).all()
    resource_ids = {r.id for r in resources}
    resource_types = {r.resource_type.lower() for r in resources}
    requests = db.query(ResourceRequest).filter(ResourceRequest.status == "pending").order_by(ResourceRequest.created_at.desc()).all()
    result = []
    for r in requests:
        matches = (not resources) or (r.requested_resource_id in resource_ids) or (r.requested_resource_id is None and (r.resource_type.lower() in resource_types or not resource_types))
        if not matches:
            continue
        matched_resource = next((x for x in resources if x.id == r.requested_resource_id), None)
        result.append({
            "id": r.id, "farmer_id": r.farmer_id, "farmer_name": r.farmer.name if r.farmer else "Farmer",
            "resource_id": matched_resource.id if matched_resource else None,
            "resource_name": matched_resource.name if matched_resource else r.resource_type.title(),
            "resource_type": r.resource_type, "crop": r.crop, "crop_stage": r.crop_stage,
            "earliest_start": r.earliest_start, "latest_end": r.latest_end,
            "duration_minutes": r.duration_minutes, "created_at": r.created_at,
            "priority": priority(r),
        })
    return result



@router.get("/{request_id}")
def get_request(request_id: int, db=Depends(get_db), user=Depends(current_user)):
    r = db.query(ResourceRequest).filter(ResourceRequest.id == request_id).first()
    if not r:
        raise HTTPException(404, "Request not found")
    if user.role == "farmer" and r.farmer_id != user.id:
        raise HTTPException(403, "Not your request")
    return {"id": r.id, "status": r.status, "priority": priority(r)}
