from fastapi import APIRouter, Depends, HTTPException
from app.core.database import get_db
from app.core.dependencies import current_user, role_required
from app.models.models import Resource
from app.schemas.common import ResourceCreate

router = APIRouter(prefix="/resources", tags=["Resources"])


@router.post("")
def create_resource(
    data: ResourceCreate,
    db=Depends(get_db),
    user=Depends(role_required("resource_owner", "admin")),
):
    resource = Resource(owner_id=user.id, **data.model_dump())
    db.add(resource)
    db.commit()
    db.refresh(resource)
    return resource


@router.get("")
def list_resources(
    resource_type: str | None = None,
    status: str | None = None,
    db=Depends(get_db),
    user=Depends(current_user),
):
    q = db.query(Resource)
    if resource_type:
        q = q.filter(Resource.resource_type.ilike(resource_type))
    if status:
        q = q.filter(Resource.status == status)
    return q.all()


@router.patch("/{resource_id}/status")
def set_status(
    resource_id: int,
    status: str,
    db=Depends(get_db),
    user=Depends(role_required("resource_owner", "admin")),
):
    resource = db.query(Resource).filter(Resource.id == resource_id).first()
    if not resource:
        raise HTTPException(404, "Resource not found")
    resource.status = status
    db.commit()
    return {"id": resource.id, "status": resource.status}
