from app.models.models import Notification


def create_notification(db, user_id, title, message, notification_type="general"):
    item = Notification(
        user_id=user_id,
        title=title,
        message=message,
        notification_type=notification_type,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item
