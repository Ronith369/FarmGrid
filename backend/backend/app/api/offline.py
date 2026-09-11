import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from app.core.database import get_db
from app.core.dependencies import current_user
from app.models.models import OfflineSyncItem

router = APIRouter(prefix="/offline", tags=["Offline Sync"])


@router.post("/sync")
def sync(data: dict, db=Depends(get_db), user=Depends(current_user)):
    results = []

    for item in data.get("items", []):
        existing = db.query(OfflineSyncItem).filter(
            OfflineSyncItem.client_id == item["client_id"]
        ).first()

        if existing:
            results.append({"client_id": item["client_id"], "status": "already_synced"})
            continue

        record = OfflineSyncItem(
            user_id=user.id,
            client_id=item["client_id"],
            action_type=item["action_type"],
            payload_json=json.dumps(item.get("payload", {})),
            status="synced",
            synced_at=datetime.now(timezone.utc),
        )
        db.add(record)
        results.append({"client_id": item["client_id"], "status": "synced"})

    db.commit()
    return {"results": results}
