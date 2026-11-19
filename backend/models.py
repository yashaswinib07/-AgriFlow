"""
Database table constants and data models for AgriFlow.
"""

# Table name definitions
TABLE_FARMERS = "farmers"
TABLE_BUYERS = "buyers"
TABLE_CROPS = "crops"
TABLE_ORDERS = "orders"
TABLE_BUYER_REQUIREMENTS = "buyer_requirements"
TABLE_REQUIREMENT_RESPONSES = "requirement_responses"
TABLE_TRANSPORTATION_RATES = "transportation_rates"

# Allowed order statuses
ORDER_STATUS_PENDING = "Pending"
ORDER_STATUS_ACCEPTED = "Accepted"
ORDER_STATUS_REJECTED = "Rejected"
ORDER_STATUS_DISPATCHED = "Dispatched"
ORDER_STATUS_DELIVERED = "Delivered"
ORDER_STATUS_COMPLETED = "Completed"

# Allowed crop categories
CROP_CATEGORIES = [
    "Grains",
    "Vegetables",
    "Fruits",
    "Pulses",
    "Oilseeds",
    "Spices",
    "Other agricultural products"
]
