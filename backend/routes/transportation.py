import sqlite3
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from database import get_db
import schemas

router = APIRouter(prefix="/api/transportation", tags=["Transportation"])

INITIAL_VEHICLES = [
    {
        "vehicle_type": "Tractor",
        "base_fare": 200.0,
        "rate_per_km": 15.0,
        "max_capacity_kg": 2000.0,
        "description": "Best for short village distances and mandi connections (up to 2,000 kg)"
    },
    {
        "vehicle_type": "Mini Truck",
        "base_fare": 350.0,
        "rate_per_km": 25.0,
        "max_capacity_kg": 3500.0,
        "description": "Economical city and district transit (e.g., Tata Ace / Bolero, up to 3,500 kg)"
    },
    {
        "vehicle_type": "Truck",
        "base_fare": 600.0,
        "rate_per_km": 40.0,
        "max_capacity_kg": 10000.0,
        "description": "Medium commercial truck for interstate & state-wide bulk transport (up to 10,000 kg)"
    },
    {
        "vehicle_type": "Large Goods Vehicle",
        "base_fare": 1000.0,
        "rate_per_km": 60.0,
        "max_capacity_kg": 25000.0,
        "description": "Heavy multi-axle carrier for high-volume enterprise wholesale shipments (up to 25,000 kg)"
    }
]


@router.get("/rates", response_model=List[schemas.TransportationRateOut])
def get_transportation_rates(conn: sqlite3.Connection = Depends(get_db)):
    """Retrieve all available vehicle types, base rates, and per-kilometer tariffs."""
    rows = conn.execute("SELECT * FROM transportation_rates").fetchall()
    if not rows:
        for item in INITIAL_VEHICLES:
            conn.execute(
                """
                INSERT INTO transportation_rates (vehicle_type, base_fare, rate_per_km, max_capacity_kg, description)
                VALUES (?, ?, ?, ?, ?)
                """,
                (item["vehicle_type"], item["base_fare"], item["rate_per_km"], item["max_capacity_kg"], item["description"])
            )
        conn.commit()
        rows = conn.execute("SELECT * FROM transportation_rates").fetchall()

    return [
        schemas.TransportationRateOut(
            id=r["id"],
            vehicle_type=r["vehicle_type"],
            base_fare=r["base_fare"],
            rate_per_km=r["rate_per_km"],
            max_capacity_kg=r["max_capacity_kg"],
            description=r["description"]
        )
        for r in rows
    ]


@router.post("/calculate", response_model=schemas.TransportationCalculationResponse)
def calculate_transportation(data: schemas.TransportationCalculationRequest, conn: sqlite3.Connection = Depends(get_db)):
    """
    Calculate full price breakdown:
    Crop amount = quantity_kg * price_per_kg
    Transport charge = base_fare + (distance_km * rate_per_km)
    Final total = Crop amount + Transport charge
    """
    rate = conn.execute(
        "SELECT * FROM transportation_rates WHERE vehicle_type = ?",
        (data.vehicle_type,)
    ).fetchone()

    if not rate:
        base_fare = 300.0
        rate_per_km = 20.0
    else:
        base_fare = rate["base_fare"]
        rate_per_km = rate["rate_per_km"]

    crop_amount = round(data.quantity_kg * data.crop_price_per_kg, 2)
    transport_charge = round(base_fare + (data.distance_km * rate_per_km), 2)
    final_amount = round(crop_amount + transport_charge, 2)

    return schemas.TransportationCalculationResponse(
        vehicle_type=data.vehicle_type,
        base_fare=base_fare,
        rate_per_km=rate_per_km,
        distance_km=data.distance_km,
        transport_charge=transport_charge,
        crop_amount=crop_amount,
        final_amount=final_amount
    )
