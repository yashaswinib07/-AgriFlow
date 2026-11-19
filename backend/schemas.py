from pydantic import BaseModel, Field
from typing import Optional, List
import datetime

# ----------------- Farmer Schemas -----------------
class FarmerRegister(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., min_length=3, max_length=120)
    phone: str = Field(..., min_length=6, max_length=20)
    password: str = Field(..., min_length=6, max_length=100)
    location: str = Field(..., min_length=2, max_length=150)  # Village or location

class FarmerLogin(BaseModel):
    email: str
    password: str

class FarmerOut(BaseModel):
    id: int
    full_name: str
    email: str
    phone: str
    location: str
    created_at: Optional[str] = None

    class Config:
        from_attributes = True

class FarmerDashboardSummary(BaseModel):
    total_crops_count: int
    total_quantity_kg: float
    estimated_earnings: float
    pending_orders_count: int
    completed_orders_count: int

# ----------------- Buyer Schemas -----------------
class BuyerRegister(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., min_length=3, max_length=120)
    phone: str = Field(..., min_length=6, max_length=20)
    password: str = Field(..., min_length=6, max_length=100)
    business_name: Optional[str] = None
    location: str = Field(..., min_length=2, max_length=150)

class BuyerLogin(BaseModel):
    email: str
    password: str

class BuyerOut(BaseModel):
    id: int
    full_name: str
    email: str
    phone: str
    business_name: Optional[str] = None
    location: str
    created_at: Optional[str] = None

    class Config:
        from_attributes = True

# ----------------- Auth Token Schema -----------------
class AuthResponse(BaseModel):
    token: str
    role: str
    user: dict

# ----------------- Crop Schemas -----------------
class CropCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    category: str = Field(..., min_length=2, max_length=50)
    image_url: Optional[str] = None
    description: Optional[str] = None
    quantity_kg: float = Field(..., gt=0)
    price_per_kg: float = Field(..., gt=0)
    discount_price_per_kg: Optional[float] = None
    quality: str = Field(..., min_length=1, max_length=50)
    crop_type: str = Field("fresh", description="fresh, surplus, or discounted")
    harvest_date: str
    location: str = Field(..., min_length=2, max_length=150)

class CropUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    image_url: Optional[str] = None
    description: Optional[str] = None
    quantity_kg: Optional[float] = None
    price_per_kg: Optional[float] = None
    discount_price_per_kg: Optional[float] = None
    quality: Optional[str] = None
    crop_type: Optional[str] = None
    harvest_date: Optional[str] = None
    location: Optional[str] = None
    is_active: Optional[bool] = None

class CropOut(BaseModel):
    id: int
    farmer_id: int
    farmer_name: Optional[str] = None
    farmer_phone: Optional[str] = None
    farmer_location: Optional[str] = None
    name: str
    category: str
    image_url: Optional[str] = None
    description: Optional[str] = None
    quantity_kg: float
    price_per_kg: float
    discount_price_per_kg: Optional[float] = None
    effective_price: float
    quality: str
    crop_type: str
    harvest_date: str
    location: str
    is_active: bool
    created_at: Optional[str] = None

    class Config:
        from_attributes = True

# ----------------- Order Schemas -----------------
class OrderCreate(BaseModel):
    crop_id: int
    quantity_kg: float = Field(..., gt=0)
    requires_transport: bool = False
    vehicle_type: Optional[str] = None
    delivery_location: str = Field(..., min_length=2)
    distance_km: Optional[float] = 0.0
    notes: Optional[str] = None

class OrderStatusUpdate(BaseModel):
    status: str = Field(..., description="Pending, Accepted, Rejected, Dispatched, Delivered, Completed")

class OrderOut(BaseModel):
    id: int
    buyer_id: int
    farmer_id: int
    crop_id: int
    crop_name: Optional[str] = None
    crop_image: Optional[str] = None
    buyer_name: Optional[str] = None
    buyer_phone: Optional[str] = None
    farmer_name: Optional[str] = None
    farmer_phone: Optional[str] = None
    quantity_kg: float
    price_per_kg: float
    crop_amount: float
    requires_transport: bool
    vehicle_type: Optional[str] = None
    delivery_location: str
    distance_km: float
    transport_charge: float
    final_amount: float
    status: str
    notes: Optional[str] = None
    created_at: Optional[str] = None

    class Config:
        from_attributes = True

# ----------------- Buyer Requirement Schemas -----------------
class RequirementCreate(BaseModel):
    crop_name: str = Field(..., min_length=2, max_length=100)
    category: str = Field(..., min_length=2, max_length=50)
    quantity_kg: float = Field(..., gt=0)
    expected_price_per_kg: float = Field(..., gt=0)
    delivery_location: str = Field(..., min_length=2, max_length=200)
    required_date: str
    requires_transport: bool = False
    description: Optional[str] = None

class RequirementResponseCreate(BaseModel):
    requirement_id: int
    offered_price_per_kg: float = Field(..., gt=0)
    available_quantity_kg: float = Field(..., gt=0)
    message: Optional[str] = None

class RequirementResponseOut(BaseModel):
    id: int
    requirement_id: int
    farmer_id: int
    farmer_name: Optional[str] = None
    farmer_phone: Optional[str] = None
    farmer_location: Optional[str] = None
    offered_price_per_kg: float
    available_quantity_kg: float
    message: Optional[str] = None
    status: str
    created_at: Optional[str] = None

    class Config:
        from_attributes = True

class RequirementOut(BaseModel):
    id: int
    buyer_id: int
    buyer_name: Optional[str] = None
    buyer_phone: Optional[str] = None
    buyer_location: Optional[str] = None
    crop_name: str
    category: str
    quantity_kg: float
    expected_price_per_kg: float
    delivery_location: str
    required_date: str
    requires_transport: bool
    description: Optional[str] = None
    status: str
    created_at: Optional[str] = None
    responses: Optional[List[RequirementResponseOut]] = []

    class Config:
        from_attributes = True

# ----------------- Transportation Schemas -----------------
class TransportationRateOut(BaseModel):
    id: int
    vehicle_type: str
    base_fare: float
    rate_per_km: float
    max_capacity_kg: float
    description: Optional[str] = None

    class Config:
        from_attributes = True

class TransportationCalculationRequest(BaseModel):
    vehicle_type: str
    distance_km: float = Field(..., ge=0)
    crop_price_per_kg: float = Field(..., ge=0)
    quantity_kg: float = Field(..., gt=0)

class TransportationCalculationResponse(BaseModel):
    vehicle_type: str
    base_fare: float
    rate_per_km: float
    distance_km: float
    transport_charge: float
    crop_amount: float
    final_amount: float
