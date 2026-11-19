import os
import sys
import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

import auth
from database import init_db, get_db_connection
from routes import farmers, buyers, crops, orders, requirements, transportation

# Initialize all SQLite database tables
init_db()

app = FastAPI(
    title="AgriFlow – Farmer and Buyer Agricultural Marketplace API",
    description="Backend API connecting farmers directly with buyers at fair, transparent prices with integrated transportation calculation.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS for frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(farmers.router)
app.include_router(buyers.router)
app.include_router(crops.router)
app.include_router(orders.router)
app.include_router(requirements.router)
app.include_router(transportation.router)

# Paths for frontend and uploads
FRONTEND_DIR = os.path.join(os.path.dirname(current_dir), "frontend")
UPLOADS_DIR = os.path.join(os.path.dirname(current_dir), "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)

if os.path.exists(UPLOADS_DIR):
    app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")


def seed_initial_data():
    """Seed sample data on first run so the marketplace is immediately interactive and full of life."""
    conn = get_db_connection()
    try:
        # 1. Transportation Rates
        t_count = conn.execute("SELECT COUNT(*) FROM transportation_rates").fetchone()[0]
        if t_count == 0:
            vehicles = [
                ("Tractor", 200.0, 15.0, 2000.0, "Best for short village distances and mandi connections (up to 2,000 kg)"),
                ("Mini Truck", 350.0, 25.0, 3500.0, "Economical city and district transit (e.g., Tata Ace / Bolero, up to 3,500 kg)"),
                ("Truck", 600.0, 40.0, 10000.0, "Medium commercial truck for interstate & state-wide bulk transport (up to 10,000 kg)"),
                ("Large Goods Vehicle", 1000.0, 60.0, 25000.0, "Heavy multi-axle carrier for high-volume enterprise wholesale shipments (up to 25,000 kg)")
            ]
            conn.executemany(
                "INSERT INTO transportation_rates (vehicle_type, base_fare, rate_per_km, max_capacity_kg, description) VALUES (?, ?, ?, ?, ?)",
                vehicles
            )
            conn.commit()

        # 2. Farmers
        f_count = conn.execute("SELECT COUNT(*) FROM farmers").fetchone()[0]
        if f_count == 0:
            now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
            
            f1_pwd = auth.hash_password("farmer123")
            f2_pwd = auth.hash_password("farmer123")

            cur = conn.cursor()
            cur.execute(
                "INSERT INTO farmers (full_name, email, phone, password_hash, location, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                ("Ramesh Patel", "ramesh@agriflow.com", "+91 98765 43210", f1_pwd, "Nashik, Maharashtra", now_iso)
            )
            f1_id = cur.lastrowid

            cur.execute(
                "INSERT INTO farmers (full_name, email, phone, password_hash, location, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                ("Suresh Kumar", "suresh@agriflow.com", "+91 98123 45678", f2_pwd, "Mandya, Karnataka", now_iso)
            )
            f2_id = cur.lastrowid

            # 3. Buyers
            b1_pwd = auth.hash_password("buyer123")
            b2_pwd = auth.hash_password("buyer123")

            cur.execute(
                "INSERT INTO buyers (full_name, email, phone, password_hash, business_name, location, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                ("Anita Sharma", "anita@freshmart.com", "+91 91234 56789", b1_pwd, "FreshMart Organics", "Bangalore, Karnataka", now_iso)
            )
            b1_id = cur.lastrowid

            cur.execute(
                "INSERT INTO buyers (full_name, email, phone, password_hash, business_name, location, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                ("Rajesh Gupta", "rajesh@greenfoods.com", "+91 99887 76655", b2_pwd, "Gupta Wholesale Traders", "Pune, Maharashtra", now_iso)
            )
            b2_id = cur.lastrowid

            # 4. Crops across all 7 categories (including prominent surplus discounts)
            crops_data = [
                (f1_id, "Organic Red Tomatoes", "Vegetables",
                 "https://images.unsplash.com/photo-1592924357228-91a4daadcfea?w=600&auto=format&fit=crop&q=80",
                 "Farm-fresh ripe and juicy hybrid tomatoes, handpicked this morning. Ideal for retail and sauce processing.",
                 850.0, 25.0, None, "Grade A", "fresh", "2026-11-15", "Nashik, Maharashtra", 1, now_iso),

                (f1_id, "Farm Surplus Potatoes", "Vegetables",
                 "https://images.unsplash.com/photo-1518977676601-b53f82aba655?w=600&auto=format&fit=crop&q=80",
                 "High quality Jyoti variety potatoes from seasonal bumper surplus. Excellent for chips, mash, and long storage. Priced low to sell fast!",
                 2200.0, 28.0, 18.0, "Grade A", "surplus", "2026-11-10", "Nashik, Maharashtra", 1, now_iso),

                (f2_id, "Sona Masoori Raw Rice", "Grains",
                 "https://images.unsplash.com/photo-1586201375761-83865001e31c?w=600&auto=format&fit=crop&q=80",
                 "Aromatic, aged premium Sona Masoori paddy processed to polished grain. Low moisture, perfect cooking texture.",
                 5000.0, 54.0, None, "Premium", "fresh", "2026-10-28", "Mandya, Karnataka", 1, now_iso),

                (f1_id, "Sharbati Golden Wheat", "Grains",
                 "https://images.unsplash.com/photo-1574323347407-f5e1ad6d020b?w=600&auto=format&fit=crop&q=80",
                 "Surplus harvest of premium Sharbati golden grains. High protein and gluten suitable for soft rotis and flour mills.",
                 3500.0, 36.0, 26.0, "Grade A", "surplus", "2026-10-20", "Nashik, Maharashtra", 1, now_iso),

                (f2_id, "Fresh Alphonso Mangoes", "Fruits",
                 "https://images.unsplash.com/photo-1553279768-865429fa0078?w=600&auto=format&fit=crop&q=80",
                 "GI tagged naturally ripened Alphonso mangoes with rich aroma and sweet pulp. Packed in ventilated crates.",
                 600.0, 140.0, None, "Export Quality", "fresh", "2026-11-14", "Ratnagiri / Mandya Hub", 1, now_iso),

                (f2_id, "Organic Desi Chickpeas (Chana)", "Pulses",
                 "https://images.unsplash.com/photo-1780648372211-0e395951c179?w=600&auto=format&fit=crop&q=80",
                 "Chemical-free unpolished brown chickpeas directly harvested and sun-dried. High fiber and protein.",
                 1200.0, 75.0, None, "Organic", "fresh", "2026-11-01", "Mandya, Karnataka", 1, now_iso),

                (f1_id, "Bold Groundnut Seeds", "Oilseeds",
                 "https://cdn.omshreegroup.com/products/peanut-bold-3540/551784059.webp",
                 "High oil content peanut seeds from surplus harvest. Cleaned and graded, ready for pressing or roasting.",
                 1800.0, 88.0, 68.0, "Grade B", "surplus", "2026-10-18", "Nashik, Maharashtra", 1, now_iso),

                (f2_id, "Guntur Stemless Red Chilli", "Spices",
                 "https://images.unsplash.com/photo-1744468714393-7d153fc04d0e?w=600&auto=format&fit=crop&q=80",
                 "Fiery red chillies with high capsaicin content and vibrant natural red color. Moisture under 10%.",
                 400.0, 190.0, None, "Grade A", "fresh", "2026-11-05", "Mandya / Guntur Hub", 1, now_iso)
            ]
            crop_ids = []
            for cd in crops_data:
                cur.execute(
                    """
                    INSERT INTO crops (
                        farmer_id, name, category, image_url, description,
                        quantity_kg, price_per_kg, discount_price_per_kg, quality,
                        crop_type, harvest_date, location, is_active, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    cd
                )
                crop_ids.append(cur.lastrowid)

            # 5. Orders
            # Order 1: Dispatched
            cur.execute(
                """
                INSERT INTO orders (
                    buyer_id, farmer_id, crop_id, quantity_kg, price_per_kg,
                    crop_amount, requires_transport, vehicle_type, delivery_location,
                    distance_km, transport_charge, final_amount, status, notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (b1_id, f1_id, crop_ids[0], 100.0, 25.0, 2500.0, 1, "Mini Truck",
                 "FreshMart Warehouse, Yeshwanthpur, Bangalore", 25.0, 975.0, 3475.0, "Dispatched",
                 "Handle crates with care. Deliver to Bay 3.", now_iso)
            )

            # Order 2: Completed (Surplus purchase)
            cur.execute(
                """
                INSERT INTO orders (
                    buyer_id, farmer_id, crop_id, quantity_kg, price_per_kg,
                    crop_amount, requires_transport, vehicle_type, delivery_location,
                    distance_km, transport_charge, final_amount, status, notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (b2_id, f1_id, crop_ids[1], 500.0, 18.0, 9000.0, 0, None,
                 "Self-pickup by buyer truck from farm", 0.0, 0.0, 9000.0, "Completed",
                 "Buyer truck arriving on Friday.", now_iso)
            )

            # Order 3: Pending
            cur.execute(
                """
                INSERT INTO orders (
                    buyer_id, farmer_id, crop_id, quantity_kg, price_per_kg,
                    crop_amount, requires_transport, vehicle_type, delivery_location,
                    distance_km, transport_charge, final_amount, status, notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (b1_id, f2_id, crop_ids[2], 250.0, 54.0, 13500.0, 1, "Tractor",
                 "APMC Yard, Mandya", 12.0, 380.0, 13880.0, "Pending",
                 "Morning delivery requested.", now_iso)
            )

            # 6. Buyer Requirements
            cur.execute(
                """
                INSERT INTO buyer_requirements (
                    buyer_id, crop_name, category, quantity_kg, expected_price_per_kg,
                    delivery_location, required_date, requires_transport, description, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'Open', ?)
                """,
                (b1_id, "Organic Baby Carrots", "Vegetables", 400.0, 35.0,
                 "Bangalore Cold Storage Hub", "2026-11-25", 1,
                 "Looking for fresh tender baby carrots washed and ready for retail packaging. Need consistent supply.", now_iso)
            )
            req1_id = cur.lastrowid

            cur.execute(
                """
                INSERT INTO buyer_requirements (
                    buyer_id, crop_name, category, quantity_kg, expected_price_per_kg,
                    delivery_location, required_date, requires_transport, description, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'Open', ?)
                """,
                (b2_id, "Finger Millet (Ragi)", "Grains", 2000.0, 42.0,
                 "Pune Grain Market", "2026-11-30", 0,
                 "Cleaned high-grade Ragi grains for whole wheat multi-grain flour milling.", now_iso)
            )

            # 7. Response to requirement
            cur.execute(
                """
                INSERT INTO requirement_responses (
                    requirement_id, farmer_id, offered_price_per_kg, available_quantity_kg, message, status, created_at
                ) VALUES (?, ?, ?, ?, ?, 'Pending', ?)
                """,
                (req1_id, f2_id, 36.0, 500.0,
                 "I have fresh organic carrots ready for harvesting next Tuesday. High sugar content and pristine quality.", now_iso)
            )

            conn.commit()

    except Exception as e:
        conn.rollback()
        print(f"Warning: Seeding encountered: {e}")
    finally:
        conn.close()


@app.on_event("startup")
def on_startup():
    seed_initial_data()


# Serve static frontend
if os.path.exists(FRONTEND_DIR):
    @app.get("/")
    def serve_home():
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    print("==================================================================")
    print("   Starting AgriFlow – Agricultural Marketplace Server")
    print("   Open your browser at: http://127.0.0.1:8000")
    print("   Interactive Swagger API Docs: http://127.0.0.1:8000/docs")
    print("==================================================================")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
