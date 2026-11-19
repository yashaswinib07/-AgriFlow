import sqlite3
import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from database import get_db
import schemas
import auth

router = APIRouter(prefix="/api/buyers", tags=["Buyers"])

@router.post("/register", response_model=schemas.AuthResponse, status_code=status.HTTP_201_CREATED)
def register_buyer(data: schemas.BuyerRegister, conn: sqlite3.Connection = Depends(get_db)):
    """Register a new buyer account and return authentication token."""
    clean_email = data.email.lower().strip()
    existing = conn.execute("SELECT id FROM buyers WHERE LOWER(email) = ?", (clean_email,)).fetchone()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A buyer with this email address already exists."
        )

    hashed_pwd = auth.hash_password(data.password)
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    cursor = conn.execute(
        """
        INSERT INTO buyers (full_name, email, phone, password_hash, business_name, location, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            data.full_name.strip(),
            clean_email,
            data.phone.strip(),
            hashed_pwd,
            data.business_name.strip() if data.business_name else None,
            data.location.strip(),
            now_iso
        )
    )
    conn.commit()
    buyer_id = cursor.lastrowid

    token = auth.create_access_token({"sub": buyer_id, "role": "buyer", "email": clean_email})
    return {
        "token": token,
        "role": "buyer",
        "user": {
            "id": buyer_id,
            "full_name": data.full_name.strip(),
            "email": clean_email,
            "phone": data.phone.strip(),
            "business_name": data.business_name.strip() if data.business_name else None,
            "location": data.location.strip()
        }
    }


@router.post("/login", response_model=schemas.AuthResponse)
def login_buyer(data: schemas.BuyerLogin, conn: sqlite3.Connection = Depends(get_db)):
    """Authenticate buyer and return session token."""
    clean_email = data.email.lower().strip()
    row = conn.execute("SELECT * FROM buyers WHERE LOWER(email) = ?", (clean_email,)).fetchone()
    if not row or not auth.verify_password(data.password, row["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password. Please check your credentials."
        )

    token = auth.create_access_token({"sub": row["id"], "role": "buyer", "email": row["email"]})
    return {
        "token": token,
        "role": "buyer",
        "user": {
            "id": row["id"],
            "full_name": row["full_name"],
            "email": row["email"],
            "phone": row["phone"],
            "business_name": row["business_name"],
            "location": row["location"]
        }
    }


@router.get("/me", response_model=schemas.BuyerOut)
def get_buyer_profile(current_buyer: dict = Depends(auth.get_current_buyer)):
    """Get profile information for the authenticated buyer."""
    return current_buyer


@router.get("/orders", response_model=List[schemas.OrderOut])
def get_buyer_orders(
    current_buyer: dict = Depends(auth.get_current_buyer),
    conn: sqlite3.Connection = Depends(get_db)
):
    """Retrieve full order history and real-time status tracking for current buyer."""
    buyer_id = current_buyer["id"]
    query = """
    SELECT 
        o.*,
        c.name as crop_name,
        c.image_url as crop_image,
        f.full_name as farmer_name,
        f.phone as farmer_phone
    FROM orders o
    LEFT JOIN crops c ON o.crop_id = c.id
    LEFT JOIN farmers f ON o.farmer_id = f.id
    WHERE o.buyer_id = ?
    ORDER BY o.id DESC
    """
    rows = conn.execute(query, (buyer_id,)).fetchall()

    result = []
    for r in rows:
        result.append(schemas.OrderOut(
            id=r["id"],
            buyer_id=r["buyer_id"],
            farmer_id=r["farmer_id"],
            crop_id=r["crop_id"],
            crop_name=r["crop_name"] or "Crop",
            crop_image=r["crop_image"],
            buyer_name=current_buyer["full_name"],
            buyer_phone=current_buyer["phone"],
            farmer_name=r["farmer_name"] or "Farmer",
            farmer_phone=r["farmer_phone"] or "",
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


@router.get("/requirements", response_model=List[schemas.RequirementOut])
def get_buyer_requirements(
    current_buyer: dict = Depends(auth.get_current_buyer),
    conn: sqlite3.Connection = Depends(get_db)
):
    """List all custom crop requirements posted by current buyer with farmer responses."""
    buyer_id = current_buyer["id"]
    req_rows = conn.execute(
        "SELECT * FROM buyer_requirements WHERE buyer_id = ? ORDER BY id DESC",
        (buyer_id,)
    ).fetchall()

    result = []
    for r in req_rows:
        resp_rows = conn.execute(
            """
            SELECT rr.*, f.full_name as farmer_name, f.phone as farmer_phone, f.location as farmer_location
            FROM requirement_responses rr
            LEFT JOIN farmers f ON rr.farmer_id = f.id
            WHERE rr.requirement_id = ?
            ORDER BY rr.id DESC
            """,
            (r["id"],)
        ).fetchall()

        responses_out = []
        for resp in resp_rows:
            responses_out.append(schemas.RequirementResponseOut(
                id=resp["id"],
                requirement_id=resp["requirement_id"],
                farmer_id=resp["farmer_id"],
                farmer_name=resp["farmer_name"] or "Farmer",
                farmer_phone=resp["farmer_phone"] or "",
                farmer_location=resp["farmer_location"] or "",
                offered_price_per_kg=resp["offered_price_per_kg"],
                available_quantity_kg=resp["available_quantity_kg"],
                message=resp["message"],
                status=resp["status"],
                created_at=None
            ))

        result.append(schemas.RequirementOut(
            id=r["id"],
            buyer_id=r["buyer_id"],
            buyer_name=current_buyer["full_name"],
            buyer_phone=current_buyer["phone"],
            buyer_location=current_buyer["location"],
            crop_name=r["crop_name"],
            category=r["category"],
            quantity_kg=r["quantity_kg"],
            expected_price_per_kg=r["expected_price_per_kg"],
            delivery_location=r["delivery_location"],
            required_date=r["required_date"],
            requires_transport=bool(r["requires_transport"]),
            description=r["description"],
            status=r["status"],
            created_at=None,
            responses=responses_out
        ))
    return result
