
import sqlite3
import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Optional
from database import get_db
import schemas
import auth

router = APIRouter(prefix="/api/crops", tags=["Crops"])


def row_to_crop_out(r: sqlite3.Row) -> schemas.CropOut:
    """Helper to convert database row to CropOut schema with effective price."""
    crop_type = r["crop_type"] if "crop_type" in r.keys() else "fresh"
    discount_price = r["discount_price_per_kg"] if "discount_price_per_kg" in r.keys() else None
    price = r["price_per_kg"]

    effective_price = (
        discount_price
        if (crop_type in ["surplus", "discounted"] and discount_price and discount_price > 0)
        else price
    )

    return schemas.CropOut(
        id=r["id"],
        farmer_id=r["farmer_id"],
        farmer_name=r["farmer_name"] if "farmer_name" in r.keys() and r["farmer_name"] else "Local Farmer",
        farmer_phone=r["farmer_phone"] if "farmer_phone" in r.keys() and r["farmer_phone"] else "",
        farmer_location=r["farmer_location"] if "farmer_location" in r.keys() and r["farmer_location"] else r["location"],
        name=r["name"],
        category=r["category"],
        image_url=r["image_url"],
        description=r["description"],
        quantity_kg=r["quantity_kg"],
        price_per_kg=price,
        discount_price_per_kg=discount_price,
        effective_price=effective_price,
        quality=r["quality"],
        crop_type=crop_type,
        harvest_date=r["harvest_date"],
        location=r["location"],
        is_active=bool(r["is_active"]),
        created_at=None
    )


@router.get("/", response_model=List[schemas.CropOut])
def get_marketplace_crops(
    search: Optional[str] = Query(None, description="Search crop name or location"),
    category: Optional[str] = Query(None, description="Category filter"),
    crop_type: Optional[str] = Query(None, description="fresh, surplus, discounted"),
    min_price: Optional[float] = Query(None, description="Minimum price per kg"),
    max_price: Optional[float] = Query(None, description="Maximum price per kg"),
    conn: sqlite3.Connection = Depends(get_db)
):
    """
    Marketplace listing endpoint:
    Browse all active crops with filters for search, category, type (fresh/surplus), and price range.
    """
    query = """
    SELECT
        c.*,
        f.full_name as farmer_name,
        f.phone as farmer_phone,
        f.location as farmer_location
    FROM crops c
    LEFT JOIN farmers f ON c.farmer_id = f.id
    WHERE c.is_active = 1 AND c.quantity_kg > 0
    """
    params = []

    if search:
        search_term = f"%{search.strip().lower()}%"
        query += " AND (LOWER(c.name) LIKE ? OR LOWER(c.location) LIKE ? OR LOWER(c.description) LIKE ?)"
        params.extend([search_term, search_term, search_term])

    if category and category.lower() != "all":
        query += " AND c.category = ?"
        params.append(category)

    if crop_type and crop_type.lower() != "all":
        query += " AND LOWER(c.crop_type) = ?"
        params.append(crop_type.lower())

    query += " ORDER BY c.id DESC"
    rows = conn.execute(query, params).fetchall()

    result = []
    for r in rows:
        out = row_to_crop_out(r)
        if min_price is not None and out.effective_price < min_price:
            continue
        if max_price is not None and out.effective_price > max_price:
            continue
        result.append(out)

    return result


@router.get("/surplus", response_model=List[schemas.CropOut])
def get_surplus_crops(conn: sqlite3.Connection = Depends(get_db)):
    """
    Dedicated endpoint for:
    SURPLUS CROPS – BUY AT LOWER PRICES
    Returns only crops marked as surplus or discounted with reduced prices.
    """
    query = """
    SELECT
        c.*,
        f.full_name as farmer_name,
        f.phone as farmer_phone,
        f.location as farmer_location
    FROM crops c
    LEFT JOIN farmers f ON c.farmer_id = f.id
    WHERE c.is_active = 1 AND c.quantity_kg > 0 AND c.crop_type IN ('surplus', 'discounted')
    ORDER BY c.id DESC
    """
    rows = conn.execute(query).fetchall()
    return [row_to_crop_out(r) for r in rows]


@router.get("/{crop_id}", response_model=schemas.CropOut)
def get_crop_details(crop_id: int, conn: sqlite3.Connection = Depends(get_db)):
    """Retrieve full details of a specific crop listing."""
    query = """
    SELECT
        c.*,
        f.full_name as farmer_name,
        f.phone as farmer_phone,
        f.location as farmer_location
    FROM crops c
    LEFT JOIN farmers f ON c.farmer_id = f.id
    WHERE c.id = ?
    """
    row = conn.execute(query, (crop_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Crop listing not found")
    return row_to_crop_out(row)


@router.post("/", response_model=schemas.CropOut, status_code=status.HTTP_201_CREATED)
def create_crop(
    data: schemas.CropCreate,
    current_farmer: dict = Depends(auth.get_current_farmer),
    conn: sqlite3.Connection = Depends(get_db)
):
    """
    Add a new crop listing (Farmer only).
    Supports marking as Fresh, Surplus, or Discounted.
    """

    # Select image based on crop name
    image_url = data.image_url

    if not image_url or not image_url.strip():
        crop_name = data.name.lower().strip()
        cat_lower = data.category.lower().strip()

        if "capsicum" in crop_name or "bell pepper" in crop_name:
            image_url = "https://images.unsplash.com/photo-1758221056967-52731a2dc935?w=600&auto=format&fit=crop&q=80"

        elif "tomato" in crop_name:
            image_url = "https://images.unsplash.com/photo-1592924357228-91a4daadcfea?w=600&auto=format&fit=crop&q=80"

        elif "potato" in crop_name:
            image_url = "https://images.unsplash.com/photo-1518977676601-b53f82aba655?w=600&auto=format&fit=crop&q=80"

        elif "rice" in crop_name:
            image_url = "https://images.unsplash.com/photo-1586201375761-83865001e31c?w=600&auto=format&fit=crop&q=80"

        elif "wheat" in crop_name:
            image_url = "https://images.unsplash.com/photo-1574323347407-f5e1ad6d020b?w=600&auto=format&fit=crop&q=80"

        elif "mango" in crop_name:
            image_url = "https://images.unsplash.com/photo-1553279768-865429fa0078?w=600&auto=format&fit=crop&q=80"

        elif "chickpea" in crop_name or "chana" in crop_name:
            image_url = "https://images.unsplash.com/photo-1515543237350-b3eea1ec8082?w=600&auto=format&fit=crop&q=80"

        elif "groundnut" in crop_name or "peanut" in crop_name:
            image_url = "https://images.unsplash.com/photo-1756694414422-30c2c8da75d2?w=600&auto=format&fit=crop&q=80"

        elif "chilli" in crop_name or "chili" in crop_name:
            image_url = "https://images.unsplash.com/photo-1596040033229-a9821ebd058d?w=600&auto=format&fit=crop&q=80"

        elif "fruit" in cat_lower:
            image_url = "https://images.unsplash.com/photo-1619566636858-adf3ef46400b?w=600&auto=format&fit=crop&q=80"

        elif "vegetable" in cat_lower:
            image_url = "https://images.unsplash.com/photo-1500937386664-56d1dfef3854?w=600&auto=format&fit=crop&q=80"

        elif "grain" in cat_lower:
            image_url = "https://images.unsplash.com/photo-1574323347407-f5e1ad6d020b?w=600&auto=format&fit=crop&q=80"

        elif "pulse" in cat_lower:
            image_url = "https://images.unsplash.com/photo-1515543237350-b3eea1ec8082?w=600&auto=format&fit=crop&q=80"

        elif "oilseed" in cat_lower:
            image_url = "https://images.unsplash.com/photo-1756694414422-30c2c8da75d2?w=600&auto=format&fit=crop&q=80"

        elif "spice" in cat_lower:
            image_url = "https://images.unsplash.com/photo-1596040033229-a9821ebd058d?w=600&auto=format&fit=crop&q=80"

        else:
            image_url = "https://images.unsplash.com/photo-1500937386664-56d1dfef3854?w=600&auto=format&fit=crop&q=80"

    crop_type = data.crop_type.lower() if data.crop_type else "fresh"
    if crop_type not in ["fresh", "surplus", "discounted"]:
        crop_type = "fresh"

    discount_price = data.discount_price_per_kg
    if crop_type in ["surplus", "discounted"] and (not discount_price or discount_price <= 0):
        discount_price = round(data.price_per_kg * 0.8, 2)

    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    cursor = conn.execute(
        """
        INSERT INTO crops (
            farmer_id, name, category, image_url, description,
            quantity_kg, price_per_kg, discount_price_per_kg, quality,
            crop_type, harvest_date, location, is_active, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
        """,
        (
            current_farmer["id"],
            data.name.strip(),
            data.category.strip(),
            image_url,
            data.description.strip() if data.description else "",
            data.quantity_kg,
            data.price_per_kg,
            discount_price,
            data.quality.strip(),
            crop_type,
            data.harvest_date,
            data.location.strip(),
            now_iso
        )
    )
    conn.commit()
    new_id = cursor.lastrowid

    # Retrieve inserted crop with farmer details
    row = conn.execute(
        """
        SELECT c.*, f.full_name as farmer_name, f.phone as farmer_phone, f.location as farmer_location
        FROM crops c
        LEFT JOIN farmers f ON c.farmer_id = f.id
        WHERE c.id = ?
        """,
        (new_id,)
    ).fetchone()

    return row_to_crop_out(row)


@router.put("/{crop_id}", response_model=schemas.CropOut)
def update_crop(
    crop_id: int,
    data: schemas.CropUpdate,
    current_farmer: dict = Depends(auth.get_current_farmer),
    conn: sqlite3.Connection = Depends(get_db)
):
    """Update details of a listed crop (Only the owner farmer can edit)."""
    crop = conn.execute("SELECT * FROM crops WHERE id = ?", (crop_id,)).fetchone()
    if not crop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Crop not found")

    if crop["farmer_id"] != current_farmer["id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only edit your own crops")

    update_dict = data.model_dump(exclude_unset=True)
    if not update_dict:
        # No changes requested
        pass
    else:
        fields = []
        vals = []
        for k, v in update_dict.items():
            fields.append(f"{k} = ?")
            vals.append(v)
        vals.append(crop_id)
        conn.execute(f"UPDATE crops SET {', '.join(fields)} WHERE id = ?", vals)

    # Reactivate if quantity > 0
    if "quantity_kg" in update_dict and update_dict["quantity_kg"] > 0:
        conn.execute("UPDATE crops SET is_active = 1 WHERE id = ?", (crop_id,))

    conn.commit()

    row = conn.execute(
        """
        SELECT c.*, f.full_name as farmer_name, f.phone as farmer_phone, f.location as farmer_location
        FROM crops c
        LEFT JOIN farmers f ON c.farmer_id = f.id
        WHERE c.id = ?
        """,
        (crop_id,)
    ).fetchone()

    return row_to_crop_out(row)


@router.delete("/{crop_id}", status_code=status.HTTP_200_OK)
def delete_crop(
    crop_id: int,
    current_farmer: dict = Depends(auth.get_current_farmer),
    conn: sqlite3.Connection = Depends(get_db)
):
    """Delete a crop listing (Only the owner farmer can delete)."""
    crop = conn.execute("SELECT * FROM crops WHERE id = ?", (crop_id,)).fetchone()
    if not crop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Crop not found")

    if crop["farmer_id"] != current_farmer["id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only delete your own crops")

    conn.execute("DELETE FROM crops WHERE id = ?", (crop_id,))
    conn.commit()
    return {"message": f"Crop '{crop['name']}' deleted successfully", "id": crop_id}

