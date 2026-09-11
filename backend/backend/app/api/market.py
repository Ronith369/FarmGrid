from fastapi import APIRouter, Depends, HTTPException
from app.core.database import get_db
from app.core.dependencies import current_user
from app.models.models import MarketOrder, YieldOffer
from app.schemas.common import MarketOrderCreate, YieldResponseCreate
from app.services.market import matching_orders

from app.services.notifications import create_notification

router = APIRouter(prefix="/market", tags=["Yield Marketplace"])


@router.post("/orders")
def create_order(data: MarketOrderCreate, db=Depends(get_db), user=Depends(current_user)):
    order = MarketOrder(buyer_id=user.id, **data.model_dump())
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


@router.get("/orders")
def orders(crop: str | None = None, db=Depends(get_db), user=Depends(current_user)):
    q = db.query(MarketOrder).filter(MarketOrder.status == "open")
    if crop:
        q = q.filter(MarketOrder.crop.ilike(crop))
    return q.order_by(MarketOrder.required_date.asc()).all()


@router.get("/orders/matches")
def matches(crop: str, quantity_kg: float, db=Depends(get_db), user=Depends(current_user)):
    return matching_orders(db, crop, quantity_kg)


@router.post("/orders/{order_id}/respond")
def respond(
    order_id: int,
    data: YieldResponseCreate,
    db=Depends(get_db),
    user=Depends(current_user),
):
    order = db.query(MarketOrder).filter(MarketOrder.id == order_id).first()
    if not order:
        raise HTTPException(404, "Order not found")
    if data.action not in {"sell", "ignore"}:
        raise HTTPException(400, "Action must be sell or ignore")

    item = YieldOffer(
        market_order_id=order.id,
        farmer_id=user.id,
        quantity_kg=data.quantity_kg,
        action=data.action,
        status="submitted" if data.action == "sell" else "ignored",
    )
    db.add(item)

    if data.action == "sell":
        # Deduct sold quantity from order quantity_kg
        sold_qty = min(order.quantity_kg, data.quantity_kg)
        order.quantity_kg = max(0.0, order.quantity_kg - sold_qty)
        if order.quantity_kg <= 0:
            order.status = "fulfilled"

        # Notify buyer of the crop sale/offer
        create_notification(
            db, order.buyer_id,
            "Crop offer/sale received",
            f"Farmer {user.name} accepted/supplied {sold_qty} kg of {order.crop}. Remaining order requirement: {order.quantity_kg} kg.",
            "market_sale",
        )

    db.commit()
    db.refresh(item)
    return {
        "offer_id": item.id,
        "action": item.action,
        "status": item.status,
        "remaining_quantity_kg": order.quantity_kg,
        "order_status": order.status,
    }


@router.post("/offers/{offer_id}/accept")
def accept_offer(offer_id: int, db=Depends(get_db), user=Depends(current_user)):
    offer_item = db.query(YieldOffer).filter(YieldOffer.id == offer_id).first()
    if not offer_item:
        raise HTTPException(404, "Yield offer not found")

    order = db.query(MarketOrder).filter(MarketOrder.id == offer_item.market_order_id).first()
    if not order:
        raise HTTPException(404, "Associated market order not found")

    offer_item.status = "accepted"
    sold_qty = min(order.quantity_kg, offer_item.quantity_kg)
    order.quantity_kg = max(0.0, order.quantity_kg - sold_qty)
    if order.quantity_kg <= 0:
        order.status = "fulfilled"

@router.post("/orders/{order_id}/buy")
def buy_crop(
    order_id: int,
    data: YieldResponseCreate,
    db=Depends(get_db),
    user=Depends(current_user),
):
    order = db.query(MarketOrder).filter(MarketOrder.id == order_id).first()
    if not order:
        raise HTTPException(404, "Crop listing not found")

    buy_qty = min(order.quantity_kg, data.quantity_kg)
    if buy_qty <= 0:
        raise HTTPException(400, "Quantity must be greater than 0")

    order.quantity_kg = max(0.0, order.quantity_kg - buy_qty)
    if order.quantity_kg <= 0:
        order.status = "fulfilled"

    item = YieldOffer(
        market_order_id=order.id,
        farmer_id=user.id,
        quantity_kg=buy_qty,
        action="buy",
        status="completed",
    )
    db.add(item)

    # Notify farmer (creator of listing) that provider bought crop produce
    create_notification(
        db, order.buyer_id,
        "Crop produce purchased!",
        f"Provider/Buyer {user.name} purchased {buy_qty} kg of your {order.crop}. Remaining listed quantity: {order.quantity_kg} kg.",
        "crop_purchased",
    )

    db.commit()
    return {
        "order_id": order.id,
        "bought_quantity_kg": buy_qty,
        "remaining_quantity_kg": order.quantity_kg,
        "status": order.status,
    }


