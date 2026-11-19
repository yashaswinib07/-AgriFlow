"""
Automated End-to-End Test Suite for AgriFlow API
Run with: python tests/test_api.py
"""

import sys
import os
import unittest
from fastapi.testclient import TestClient

# Add backend directory to sys.path
backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from main import app, seed_initial_data

class AgriFlowApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        # Seed initial data
        seed_initial_data()

    def test_01_docs_accessible(self):
        """Test Swagger documentation is accessible."""
        response = self.client.get("/docs")
        self.assertEqual(response.status_code, 200)

    def test_02_farmer_login(self):
        """Test logging in with seeded sample farmer."""
        response = self.client.post("/api/farmers/login", json={
            "email": "ramesh@agriflow.com",
            "password": "farmer123"
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("token", data)
        self.assertEqual(data["role"], "farmer")
        self.assertEqual(data["user"]["full_name"], "Ramesh Patel")

    def test_03_buyer_login(self):
        """Test logging in with seeded sample buyer."""
        response = self.client.post("/api/buyers/login", json={
            "email": "anita@freshmart.com",
            "password": "buyer123"
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("token", data)
        self.assertEqual(data["role"], "buyer")
        self.assertEqual(data["user"]["full_name"], "Anita Sharma")

    def test_04_marketplace_listing_and_surplus(self):
        """Test browsing marketplace crops and surplus deals."""
        response = self.client.get("/api/crops/")
        self.assertEqual(response.status_code, 200)
        crops = response.json()
        self.assertGreater(len(crops), 0)

        # Check surplus endpoint
        surplus_res = self.client.get("/api/crops/surplus")
        self.assertEqual(surplus_res.status_code, 200)
        surplus_crops = surplus_res.json()
        self.assertGreater(len(surplus_crops), 0)
        for sc in surplus_crops:
            self.assertIn(sc["crop_type"], ["surplus", "discounted"])
            self.assertIsNotNone(sc["discount_price_per_kg"])
            self.assertLess(sc["effective_price"], sc["price_per_kg"])

    def test_05_transportation_rates_and_calculation(self):
        """Test transportation rates and interactive price breakdown calculation."""
        rates_res = self.client.get("/api/transportation/rates")
        self.assertEqual(rates_res.status_code, 200)
        rates = rates_res.json()
        self.assertGreaterEqual(len(rates), 4)

        # Calculation test: Mini Truck for 20 km, 100 kg at Rs 20/kg
        # Crop amount = 100 * 20 = 2000
        # Mini Truck: base = 350, per_km = 25 -> 350 + (20 * 25) = 850
        # Total = 2850
        calc_res = self.client.post("/api/transportation/calculate", json={
            "vehicle_type": "Mini Truck",
            "distance_km": 20.0,
            "crop_price_per_kg": 20.0,
            "quantity_kg": 100.0
        })
        self.assertEqual(calc_res.status_code, 200)
        calc = calc_res.json()
        self.assertEqual(calc["crop_amount"], 2000.0)
        self.assertEqual(calc["transport_charge"], 850.0)
        self.assertEqual(calc["final_amount"], 2850.0)

    def test_06_farmer_add_crop_and_dashboard_summary(self):
        """Test farmer adding a crop and viewing dashboard summary."""
        # Login
        f_login = self.client.post("/api/farmers/login", json={
            "email": "ramesh@agriflow.com",
            "password": "farmer123"
        }).json()
        token = f_login["token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Add new crop
        crop_payload = {
            "name": "Fresh Green Capsicum",
            "category": "Vegetables",
            "quantity_kg": 300.0,
            "price_per_kg": 40.0,
            "discount_price_per_kg": 30.0,
            "quality": "Grade A",
            "crop_type": "surplus",
            "harvest_date": "2026-11-18",
            "location": "Nashik, Maharashtra",
            "description": "Crisp green bell peppers directly from greenhouse."
        }
        create_res = self.client.post("/api/crops/", json=crop_payload, headers=headers)
        self.assertEqual(create_res.status_code, 201)
        created_crop = create_res.json()
        self.assertEqual(created_crop["name"], "Fresh Green Capsicum")
        self.assertEqual(created_crop["effective_price"], 30.0)

        # Check dashboard summary
        summary_res = self.client.get("/api/farmers/dashboard-summary", headers=headers)
        self.assertEqual(summary_res.status_code, 200)
        summary = summary_res.json()
        self.assertGreater(summary["total_crops_count"], 0)
        self.assertGreater(summary["total_quantity_kg"], 0)
        self.assertGreater(summary["estimated_earnings"], 0)

    def test_07_buyer_order_creation_and_stock_deduction(self):
        """Test buyer placing an order with transportation and verifying stock deduction."""
        # 1. Get a crop to purchase
        crops = self.client.get("/api/crops/").json()
        target_crop = crops[0]
        initial_stock = target_crop["quantity_kg"]

        # 2. Login buyer
        b_login = self.client.post("/api/buyers/login", json={
            "email": "anita@freshmart.com",
            "password": "buyer123"
        }).json()
        b_token = b_login["token"]
        b_headers = {"Authorization": f"Bearer {b_token}"}

        # 3. Place order for 50 kg
        order_payload = {
            "crop_id": target_crop["id"],
            "quantity_kg": 50.0,
            "requires_transport": True,
            "vehicle_type": "Mini Truck",
            "delivery_location": "Bangalore Central Market",
            "distance_km": 15.0,
            "notes": "Urgent morning delivery."
        }
        order_res = self.client.post("/api/orders/", json=order_payload, headers=b_headers)
        self.assertEqual(order_res.status_code, 201)
        order = order_res.json()
        self.assertEqual(order["quantity_kg"], 50.0)
        self.assertEqual(order["status"], "Pending")
        self.assertGreater(order["transport_charge"], 0)
        self.assertEqual(order["final_amount"], order["crop_amount"] + order["transport_charge"])

        # 4. Check crop stock was deducted
        updated_crop = self.client.get(f"/api/crops/{target_crop['id']}").json()
        self.assertEqual(updated_crop["quantity_kg"], initial_stock - 50.0)

    def test_08_order_status_update_by_farmer(self):
        """Test farmer accepting and dispatching orders."""
        # Farmer login
        f_login = self.client.post("/api/farmers/login", json={
            "email": "ramesh@agriflow.com",
            "password": "farmer123"
        }).json()
        f_headers = {"Authorization": f"Bearer {f_login['token']}"}

        # Get farmer orders
        orders = self.client.get("/api/farmers/orders", headers=f_headers).json()
        self.assertGreater(len(orders), 0)
        first_order = orders[0]

        # Update status to Accepted
        update_res = self.client.put(
            f"/api/orders/{first_order['id']}/status",
            json={"status": "Accepted"},
            headers=f_headers
        )
        self.assertEqual(update_res.status_code, 200)
        self.assertEqual(update_res.json()["status"], "Accepted")

    def test_09_buyer_requirement_and_farmer_response(self):
        """Test buyer posting crop requirement and farmer responding."""
        # Buyer login
        b_login = self.client.post("/api/buyers/login", json={
            "email": "anita@freshmart.com",
            "password": "buyer123"
        }).json()
        b_headers = {"Authorization": f"Bearer {b_login['token']}"}

        # Post requirement
        req_payload = {
            "crop_name": "Premium Basmati Rice 1121",
            "category": "Grains",
            "quantity_kg": 1500.0,
            "expected_price_per_kg": 85.0,
            "delivery_location": "FreshMart Mega Hub, Whitefield",
            "required_date": "2026-12-05",
            "requires_transport": True,
            "description": "Aged extra long grain Basmati required for premium packaging."
        }
        create_req_res = self.client.post("/api/requirements/", json=req_payload, headers=b_headers)
        self.assertEqual(create_req_res.status_code, 201)
        created_req = create_req_res.json()
        req_id = created_req["id"]

        # Farmer responds
        f_login = self.client.post("/api/farmers/login", json={
            "email": "suresh@agriflow.com",
            "password": "farmer123"
        }).json()
        f_headers = {"Authorization": f"Bearer {f_login['token']}"}

        resp_payload = {
            "requirement_id": req_id,
            "offered_price_per_kg": 84.0,
            "available_quantity_kg": 2000.0,
            "message": "We have export grade 1121 Basmati paddy currently aged 12 months. Ready to dispatch."
        }
        resp_res = self.client.post("/api/requirements/respond", json=resp_payload, headers=f_headers)
        self.assertEqual(resp_res.status_code, 201)

        # Buyer verifies response is visible
        buyer_reqs = self.client.get("/api/buyers/requirements", headers=b_headers).json()
        matching = [r for r in buyer_reqs if r["id"] == req_id]
        self.assertEqual(len(matching), 1)
        self.assertGreaterEqual(len(matching[0]["responses"]), 1)
        self.assertEqual(matching[0]["responses"][0]["offered_price_per_kg"], 84.0)


if __name__ == "__main__":
    unittest.main()
