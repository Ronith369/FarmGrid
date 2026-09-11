from fastapi import APIRouter, Depends
from app.core.database import get_db
from app.core.dependencies import current_user
from app.models.models import Notification

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("")
def list_notifications(db=Depends(get_db), user=Depends(current_user)):
    return db.query(Notification).filter(
        Notification.user_id == user.id
    ).order_by(Notification.created_at.desc()).all()


@router.post("/{notification_id}/read")
def mark_read(notification_id: int, db=Depends(get_db), user=Depends(current_user)):
    item = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == user.id,
    ).first()
    if not item:
        return {"error": "Notification not found"}
    item.is_read = True
    db.commit()
    return {"id": item.id, "is_read": True}
