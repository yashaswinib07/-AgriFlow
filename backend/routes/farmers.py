import sqlite3
import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from database import get_db
import schemas
import auth

router = APIRouter(prefix="/api/farmers", tags=["Farmers"])

@router.post("/register", response_model=schemas.AuthResponse, status_code=status.HTTP_201_CREATED)
def register_farmer(data: schemas.FarmerRegister, conn: sqlite3.Connection = Depends(get_db)):
    """Register a new farmer account and return authentication token."""
    clean_email = data.email.lower().strip()
    existing = conn.execute("SELECT id FROM farmers WHERE LOWER(email) = ?", (clean_email,)).fetchone()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A farmer with this email address already exists."
        )

    hashed_pwd = auth.hash_password(data.password)
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    cursor = conn.execute(
        """
        INSERT INTO farmers (full_name, email, phone, password_hash, location, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (data.full_name.strip(), clean_email, data.phone.strip(), hashed_pwd, data.location.strip(), now_iso)
    )
    conn.commit()
    farmer_id = cursor.lastrowid

    token = auth.create_access_token({"sub": farmer_id, "role": "farmer", "email": clean_email})
    return {
        "token": token,
        "role": "farmer",
        "user": {
            "id": farmer_id,
            "full_name": data.full_name.strip(),
            "email": clean_email,
            "phone": data.phone.strip(),
            "location": data.location.strip()
        }
    }


@router.post("/login", response_model=schemas.AuthResponse)
def login_farmer(data: schemas.FarmerLogin, conn: sqlite3.Connection = Depends(get_db)):
    """Authenticate farmer and return session token."""
    clean_email = data.email.lower().strip()
    row = conn.execute("SELECT * FROM farmers WHERE LOWER(email) = ?", (clean_email,)).fetchone()
    if not row or not auth.verify_password(data.password, row["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password. Please check your credentials."
        )

    token = auth.create_access_token({"sub": row["id"], "role": "farmer", "email": row["email"]})
    return {
        "token": token,
        "role": "farmer",
        "user": {
            "id": row["id"],
            "full_name": row["full_name"],
            "email": row["email"],
            "phone": row["phone"],
            "location": row["location"]
        }
    }


@router.get("/me", response_model=schemas.FarmerOut)
def get_farmer_profile(current_farmer: dict = Depends(auth.get_current_farmer)):
    """Get profile information for the authenticated farmer."""
    return current_farmer


@router.get("/dashboard-summary", response_model=schemas.FarmerDashboardSummary)
def get_farmer_dashboard_summary(
    current_farmer: dict = Depends(auth.get_current_farmer),
    conn: sqlite3.Connection = Depends(get_db)
):
    """
    Compute dashboard statistics:
    - Total crops listed
    - Total quantity in stock (kg)
    - Estimated potential earnings from listed stock + realized orders
    - Pending incoming orders count
    - Completed orders count
    """
    farmer_id = current_farmer["id"]
    crop_rows = conn.execute(
        "SELECT quantity_kg, price_per_kg, discount_price_per_kg, crop_type FROM crops WHERE farmer_id = ? AND is_active = 1",
        (farmer_id,)
    ).fetchall()

    total_crops_count = len(crop_rows)
    total_quantity_kg = sum(r["quantity_kg"] for r in crop_rows)

    potential_stock_value = 0.0
    for r in crop_rows:
        price = (
            r["discount_price_per_kg"]
            if (r["crop_type"] in ["surplus", "discounted"] and r["discount_price_per_kg"] and r["discount_price_per_kg"] > 0)
            else r["price_per_kg"]
        )
        potential_stock_value += r["quantity_kg"] * price

    realized_row = conn.execute(
        """
        SELECT COALESCE(SUM(crop_amount), 0) as total_earned
        FROM orders
        WHERE farmer_id = ? AND status IN ('Accepted', 'Dispatched', 'Delivered', 'Completed')
        """,
        (farmer_id,)
    ).fetchone()
    realized_earnings = realized_row["total_earned"] if realized_row else 0.0

    pending_row = conn.execute(
        "SELECT COUNT(*) as cnt FROM orders WHERE farmer_id = ? AND status = 'Pending'",
        (farmer_id,)
    ).fetchone()
    pending_count = pending_row["cnt"] if pending_row else 0

    completed_row = conn.execute(
        "SELECT COUNT(*) as cnt FROM orders WHERE farmer_id = ? AND status IN ('Delivered', 'Completed')",
        (farmer_id,)
    ).fetchone()
    completed_count = completed_row["cnt"] if completed_row else 0

    estimated_earnings = round(potential_stock_value + realized_earnings, 2)

    return {
        "total_crops_count": total_crops_count,
        "total_quantity_kg": round(total_quantity_kg, 2),
        "estimated_earnings": estimated_earnings,
        "pending_orders_count": pending_count,
        "completed_orders_count": completed_count
    }


@router.get("/crops", response_model=List[schemas.CropOut])
def get_farmer_crops(
    current_farmer: dict = Depends(auth.get_current_farmer),
    conn: sqlite3.Connection = Depends(get_db)
):
    """List all crops owned by current farmer."""
    farmer_id = current_farmer["id"]
    rows = conn.execute(
        "SELECT * FROM crops WHERE farmer_id = ? ORDER BY id DESC",
        (farmer_id,)
    ).fetchall()

    result = []
    for r in rows:
        eff_price = (
            r["discount_price_per_kg"]
            if (r["crop_type"] in ["surplus", "discounted"] and r["discount_price_per_kg"] and r["discount_price_per_kg"] > 0)
            else r["price_per_kg"]
        )
        result.append(schemas.CropOut(
            id=r["id"],
            farmer_id=farmer_id,
            farmer_name=current_farmer["full_name"],
            farmer_phone=current_farmer["phone"],
            farmer_location=current_farmer["location"],
            name=r["name"],
            category=r["category"],
            image_url=r["image_url"],
            description=r["description"],
            quantity_kg=r["quantity_kg"],
            price_per_kg=r["price_per_kg"],
            discount_price_per_kg=r["discount_price_per_kg"],
            effective_price=eff_price,
            quality=r["quality"],
            crop_type=r["crop_type"],
            harvest_date=r["harvest_date"],
            location=r["location"],
            is_active=bool(r["is_active"]),
            created_at=None
        ))
    return result


@router.get("/orders", response_model=List[schemas.OrderOut])
def get_farmer_orders(
    current_farmer: dict = Depends(auth.get_current_farmer),
    conn: sqlite3.Connection = Depends(get_db)
):
    """List all buyer orders received for this farmer's crops."""
    farmer_id = current_farmer["id"]
    query = """
    SELECT 
        o.*,
        c.name as crop_name,
        c.image_url as crop_image,
        b.full_name as buyer_name,
        b.phone as buyer_phone
    FROM orders o
    LEFT JOIN crops c ON o.crop_id = c.id
    LEFT JOIN buyers b ON o.buyer_id = b.id
    WHERE o.farmer_id = ?
    ORDER BY o.id DESC
    """
    rows = conn.execute(query, (farmer_id,)).fetchall()

    result = []
    for r in rows:
        result.append(schemas.OrderOut(
            id=r["id"],
            buyer_id=r["buyer_id"],
            farmer_id=r["farmer_id"],
            crop_id=r["crop_id"],
            crop_name=r["crop_name"] or "Crop",
            crop_image=r["crop_image"],
            buyer_name=r["buyer_name"] or "Buyer",
            buyer_phone=r["buyer_phone"] or "",
            farmer_name=current_farmer["full_name"],
            farmer_phone=current_farmer["phone"],
            quantity_kg=r["quantity_kg"],
            price_per_kg=r["price_per_kg"],
            crop_amount=r["crop_amount"],
            requires_transport=bool(r["requires_transport"]),
            vehicle_type=r["vehicle_type"],
            delivery_location=r["delivery_location"],
            distance_km=r["distance_km"],
            transport_charge=r["transport_charge"],
            final_amount=r["final_amount"],
            status=r["status"],
            notes=r["notes"],
            created_at=None
        ))
    return result
