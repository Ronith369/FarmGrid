from app.models.models import MarketOrder


def matching_orders(db, crop, quantity_kg):
    return (
        db.query(MarketOrder)
        .filter(
            MarketOrder.crop.ilike(crop),
            MarketOrder.quantity_kg <= quantity_kg,
            MarketOrder.status == "open",
        )
        .all()
    )
