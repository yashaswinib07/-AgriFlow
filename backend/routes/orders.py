import sqlite3
import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from database import get_db
import schemas
import auth

router = APIRouter(prefix="/api/orders", tags=["Orders"])

DEFAULT_RATES = {
    "Tractor": {"base": 200.0, "per_km": 15.0},
    "Mini Truck": {"base": 350.0, "per_km": 25.0},
    "Truck": {"base": 600.0, "per_km": 40.0},
    "Large Goods Vehicle": {"base": 1000.0, "per_km": 60.0}
}


def compute_transport_charge(vehicle_type: str, distance_km: float, conn: sqlite3.Connection) -> float:
    """Calculate transport cost from database rate or default lookup."""
    rate_record = conn.execute(
        "SELECT * FROM transportation_rates WHERE vehicle_type = ?",
        (vehicle_type,)
    ).fetchone()

    if rate_record:
        base = rate_record["base_fare"]
        per_km = rate_record["rate_per_km"]
    else:
        info = DEFAULT_RATES.get(vehicle_type, {"base": 300.0, "per_km": 20.0})
        base = info["base"]
        per_km = info["per_km"]

    return round(base + (distance_km * per_km), 2)


@router.post("/", response_model=schemas.OrderOut, status_code=status.HTTP_201_CREATED)
def create_order(
    order_data: schemas.OrderCreate,
    current_buyer: dict = Depends(auth.get_current_buyer),
    conn: sqlite3.Connection = Depends(get_db)
):
    """
    Place an order for a listed crop:
    - Checks stock availability
    - Calculates effective price (original vs surplus discount)
    - Computes transportation charges if buyer requested transport
    - Calculates total crop amount and final amount
    - Automatically updates crop inventory stock
    """
    crop = conn.execute("SELECT * FROM crops WHERE id = ?", (order_data.crop_id,)).fetchone()
    if not crop or not crop["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The selected crop is not available for purchase."
        )

    # Stock validation
    if order_data.quantity_kg > crop["quantity_kg"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Requested quantity ({order_data.quantity_kg} kg) exceeds available stock ({crop['quantity_kg']} kg)."
        )

    # Effective price per kg
    price_per_kg = (
        crop["discount_price_per_kg"]
        if (crop["crop_type"] in ["surplus", "discounted"] and crop["discount_price_per_kg"] and crop["discount_price_per_kg"] > 0)
        else crop["price_per_kg"]
    )

    crop_amount = round(order_data.quantity_kg * price_per_kg, 2)
    transport_charge = 0.0

    if order_data.requires_transport:
        vehicle = order_data.vehicle_type or "Mini Truck"
        dist = max(order_data.distance_km or 10.0, 1.0)
        transport_charge = compute_transport_charge(vehicle, dist, conn)
    else:
        order_data.vehicle_type = None
        order_data.distance_km = 0.0

    final_amount = round(crop_amount + transport_charge, 2)

    # Deduct crop quantity stock
    new_quantity = round(crop["quantity_kg"] - order_data.quantity_kg, 2)
    is_active = 1 if new_quantity > 0 else 0
    conn.execute(
        "UPDATE crops SET quantity_kg = ?, is_active = ? WHERE id = ?",
        (new_quantity, is_active, crop["id"])
    )

    # Insert order
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    cursor = conn.execute(
        """
        INSERT INTO orders (
            buyer_id, farmer_id, crop_id, quantity_kg, price_per_kg,
            crop_amount, requires_transport, vehicle_type, delivery_location,
            distance_km, transport_charge, final_amount, status, notes, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pending', ?, ?)
        """,
        (
            current_buyer["id"],
            crop["farmer_id"],
            crop["id"],
            order_data.quantity_kg,
            price_per_kg,
            crop_amount,
            1 if order_data.requires_transport else 0,
            order_data.vehicle_type,
            order_data.delivery_location.strip(),
            order_data.distance_km or 0.0,
            transport_charge,
            final_amount,
            order_data.notes,
            now_iso
        )
    )
    conn.commit()
    order_id = cursor.lastrowid

    # Fetch farmer name
    farmer = conn.execute("SELECT full_name, phone FROM farmers WHERE id = ?", (crop["farmer_id"],)).fetchone()

    return schemas.OrderOut(
        id=order_id,
        buyer_id=current_buyer["id"],
        farmer_id=crop["farmer_id"],
        crop_id=crop["id"],
        crop_name=crop["name"],
        crop_image=crop["image_url"],
        buyer_name=current_buyer["full_name"],
        buyer_phone=current_buyer["phone"],
        farmer_name=farmer["full_name"] if farmer else "Farmer",
        farmer_phone=farmer["phone"] if farmer else "",
        quantity_kg=order_data.quantity_kg,
        price_per_kg=price_per_kg,
        crop_amount=crop_amount,
        requires_transport=order_data.requires_transport,
        vehicle_type=order_data.vehicle_type,
        delivery_location=order_data.delivery_location.strip(),
        distance_km=order_data.distance_km or 0.0,
        transport_charge=transport_charge,
        final_amount=final_amount,
        status="Pending",
        notes=order_data.notes,
        created_at=None
    )


@router.get("/{order_id}", response_model=schemas.OrderOut)
def get_order_by_id(order_id: int, conn: sqlite3.Connection = Depends(get_db)):
    """Retrieve full details of an individual order."""
    query = """
    SELECT 
        o.*,
        c.name as crop_name,
        c.image_url as crop_image,
        b.full_name as buyer_name,
        b.phone as buyer_phone,
        f.full_name as farmer_name,
        f.phone as farmer_phone
    FROM orders o
    LEFT JOIN crops c ON o.crop_id = c.id
    LEFT JOIN buyers b ON o.buyer_id = b.id
    LEFT JOIN farmers f ON o.farmer_id = f.id
    WHERE o.id = ?
    """
    row = conn.execute(query, (order_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    return schemas.OrderOut(
        id=row["id"],
        buyer_id=row["buyer_id"],
        farmer_id=row["farmer_id"],
        crop_id=row["crop_id"],
        crop_name=row["crop_name"] or "Crop",
        crop_image=row["crop_image"],
        buyer_name=row["buyer_name"] or "Buyer",
        buyer_phone=row["buyer_phone"] or "",
        farmer_name=row["farmer_name"] or "Farmer",
        farmer_phone=row["farmer_phone"] or "",
        quantity_kg=row["quantity_kg"],
        price_per_kg=row["price_per_kg"],
        crop_amount=row["crop_amount"],
        requires_transport=bool(row["requires_transport"]),
        vehicle_type=row["vehicle_type"],
        delivery_location=row["delivery_location"],
        distance_km=row["distance_km"],
        transport_charge=row["transport_charge"],
        final_amount=row["final_amount"],
        status=row["status"],
        notes=row["notes"],
        created_at=None
    )


@router.put("/{order_id}/status", response_model=schemas.OrderOut)
def update_order_status(
    order_id: int,
    status_update: schemas.OrderStatusUpdate,
    current_farmer: dict = Depends(auth.get_current_farmer),
    conn: sqlite3.Connection = Depends(get_db)
):
    """
    Farmer updates order status:
    Allowed: 'Pending', 'Accepted', 'Rejected', 'Dispatched', 'Delivered', 'Completed'
    If rejected, restores crop stock to available inventory.
    """
    order = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    if order["farmer_id"] != current_farmer["id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only manage orders for your crops")

    valid_statuses = ["Pending", "Accepted", "Rejected", "Dispatched", "Delivered", "Completed"]
    new_status = status_update.status.capitalize()
    if new_status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status '{status_update.status}'. Valid choices are: {', '.join(valid_statuses)}"
        )

    old_status = order["status"]

    # If transitioning to Rejected from any non-rejected state, restore crop quantity
    if new_status == "Rejected" and old_status != "Rejected":
        conn.execute(
            "UPDATE crops SET quantity_kg = quantity_kg + ?, is_active = 1 WHERE id = ?",
            (order["quantity_kg"], order["crop_id"])
        )

    # If re-accepting a previously rejected order, deduct stock back if available
    elif old_status == "Rejected" and new_status in ["Accepted", "Pending", "Dispatched"]:
        crop = conn.execute("SELECT quantity_kg FROM crops WHERE id = ?", (order["crop_id"],)).fetchone()
        if crop and crop["quantity_kg"] >= order["quantity_kg"]:
            new_qty = crop["quantity_kg"] - order["quantity_kg"]
            conn.execute(
                "UPDATE crops SET quantity_kg = ?, is_active = ? WHERE id = ?",
                (new_qty, 1 if new_qty > 0 else 0, order["crop_id"])
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot reinstate order: insufficient crop stock currently available."
            )

    conn.execute("UPDATE orders SET status = ? WHERE id = ?", (new_status, order_id))
    conn.commit()

    return get_order_by_id(order_id, conn)
