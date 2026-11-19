import sqlite3
import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from database import get_db
import schemas
import auth

router = APIRouter(prefix="/api/requirements", tags=["Requirements"])


@router.get("/", response_model=List[schemas.RequirementOut])
def get_all_requirements(conn: sqlite3.Connection = Depends(get_db)):
    """
    Public / Farmer view of all posted buyer crop requirements.
    Allows farmers to see what crops are currently demanded by buyers.
    """
    query = """
    SELECT 
        r.*,
        b.full_name as buyer_name,
        b.phone as buyer_phone,
        b.location as buyer_location
    FROM buyer_requirements r
    LEFT JOIN buyers b ON r.buyer_id = b.id
    ORDER BY r.id DESC
    """
    req_rows = conn.execute(query).fetchall()

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
            buyer_name=r["buyer_name"] or "Buyer",
            buyer_phone=r["buyer_phone"] or "",
            buyer_location=r["buyer_location"] or "",
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


@router.post("/", response_model=schemas.RequirementOut, status_code=status.HTTP_201_CREATED)
def create_requirement(
    data: schemas.RequirementCreate,
    current_buyer: dict = Depends(auth.get_current_buyer),
    conn: sqlite3.Connection = Depends(get_db)
):
    """
    Buyer posts a custom crop requirement for crops not yet in the marketplace.
    """
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    cursor = conn.execute(
        """
        INSERT INTO buyer_requirements (
            buyer_id, crop_name, category, quantity_kg, expected_price_per_kg,
            delivery_location, required_date, requires_transport, description, status, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'Open', ?)
        """,
        (
            current_buyer["id"],
            data.crop_name.strip(),
            data.category.strip(),
            data.quantity_kg,
            data.expected_price_per_kg,
            data.delivery_location.strip(),
            data.required_date,
            1 if data.requires_transport else 0,
            data.description.strip() if data.description else "",
            now_iso
        )
    )
    conn.commit()
    new_id = cursor.lastrowid

    return schemas.RequirementOut(
        id=new_id,
        buyer_id=current_buyer["id"],
        buyer_name=current_buyer["full_name"],
        buyer_phone=current_buyer["phone"],
        buyer_location=current_buyer["location"],
        crop_name=data.crop_name.strip(),
        category=data.category.strip(),
        quantity_kg=data.quantity_kg,
        expected_price_per_kg=data.expected_price_per_kg,
        delivery_location=data.delivery_location.strip(),
        required_date=data.required_date,
        requires_transport=data.requires_transport,
        description=data.description.strip() if data.description else "",
        status="Open",
        created_at=None,
        responses=[]
    )


@router.post("/respond", response_model=schemas.RequirementResponseOut, status_code=status.HTTP_201_CREATED)
def farmer_respond_to_requirement(
    data: schemas.RequirementResponseCreate,
    current_farmer: dict = Depends(auth.get_current_farmer),
    conn: sqlite3.Connection = Depends(get_db)
):
    """
    Farmers respond to a buyer's requirement with their available quantity and price offer.
    """
    req = conn.execute("SELECT id FROM buyer_requirements WHERE id = ?", (data.requirement_id,)).fetchone()
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buyer requirement not found")

    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    cursor = conn.execute(
        """
        INSERT INTO requirement_responses (
            requirement_id, farmer_id, offered_price_per_kg, available_quantity_kg, message, status, created_at
        ) VALUES (?, ?, ?, ?, ?, 'Pending', ?)
        """,
        (
            data.requirement_id,
            current_farmer["id"],
            data.offered_price_per_kg,
            data.available_quantity_kg,
            data.message.strip() if data.message else "I have this crop ready for dispatch.",
            now_iso
        )
    )
    conn.commit()
    resp_id = cursor.lastrowid

    return schemas.RequirementResponseOut(
        id=resp_id,
        requirement_id=data.requirement_id,
        farmer_id=current_farmer["id"],
        farmer_name=current_farmer["full_name"],
        farmer_phone=current_farmer["phone"],
        farmer_location=current_farmer["location"],
        offered_price_per_kg=data.offered_price_per_kg,
        available_quantity_kg=data.available_quantity_kg,
        message=data.message.strip() if data.message else "I have this crop ready for dispatch.",
        status="Pending",
        created_at=None
    )
