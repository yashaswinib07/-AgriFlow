# 🌱 AgriFlow – Farmer and Buyer Agricultural Marketplace

AgriFlow is a full-stack, direct farm-to-table agricultural marketplace that connects farmers directly with wholesale and retail buyers. Farmers can sell fresh produce and seasonal surplus at custom prices, and buyers can purchase crops at fair rates with transparent, calculated transportation.

---

## 🌟 Key Features

1. **Attractive Green-and-White Agricultural Theme**: Clean, responsive, and intuitive interface designed specifically for agricultural workflows.
2. **Completely Separate Portals**:
   - **Farmer Portal**: Registration with village/location, crop inventory management, order fulfillment, and earnings summary.
   - **Buyer Portal**: Registration with business details, marketplace browsing, order placement, order tracking, and custom demand requests.
3. **Surplus Produce Section**:
   - Farmers can mark crops as **Fresh Crop**, **Surplus Crop**, or **Discounted Crop**.
   - Farmers can specify a discounted price for surplus crops.
   - Prominently showcases discounted surplus crops in a dedicated **SURPLUS CROPS – BUY AT LOWER PRICES** section.
4. **Interactive Transportation Calculator**:
   - Buyers choose whether they require transport or will arrange self-pickup.
   - If **Yes**, buyers select from available commercial vehicles:
     - **Tractor**: Base ₹200 + ₹15/km (up to 2,000 kg)
     - **Mini Truck**: Base ₹350 + ₹25/km (up to 3,500 kg)
     - **Truck**: Base ₹600 + ₹40/km (up to 10,000 kg)
     - **Large Goods Vehicle**: Base ₹1,000 + ₹60/km (up to 25,000 kg)
   - Clear price breakdown displayed before ordering:
     $$\text{Crop Quantity} \times \text{Price per kg} = \text{Crop Amount}$$
     $$\text{Crop Amount} + \text{Transportation Charge} = \text{Final Total}$$
5. **Buyer Requirement Request System**:
   - Buyers can post crops not currently listed in the marketplace.
   - Farmers can browse requirements and submit direct quotations with offered price and quantity.
   - Buyers view farmer quotations in real-time.
6. **Complete Order Lifecycle Management**:
   - Status transitions: `Pending` → `Accepted` → `Dispatched` → `Delivered` → `Completed` (or `Rejected`).
   - Automatic stock quantity deduction with validation.
   - Stock auto-replenishment if an order is rejected.
7. **Interactive API Documentation**: Built-in Swagger UI at `/docs`.
8. **Docker & Docker Compose**: 1-command containerization for easy deployment.

---

## 🛠️ Technology Stack

- **Frontend**: HTML5, CSS3, JavaScript (Vanilla ES6+), SVG icons, and responsive layouts.
- **Backend**: Python FastAPI (Asynchronous REST API).
- **Database**: SQLite (Zero-configuration, permanent local storage, pure-Python data access).
- **API Documentation**: OpenAPI / Swagger (`/docs`) and ReDoc (`/redoc`).
- **Containerization**: Dockerfile and `docker-compose.yml`.

---

## 📁 Project Structure

```text
AgriFlow/
├── backend/
│   ├── main.py              # FastAPI application entrypoint & static file server
│   ├── database.py          # SQLite connection and table initialization
│   ├── models.py            # Table definitions and status constants
│   ├── schemas.py           # Pydantic request/response validation schemas
│   ├── auth.py              # Password hashing (PBKDF2) & HMAC session tokens
│   ├── routes/
│   │   ├── farmers.py       # Farmer auth, profile, crops & orders endpoints
│   │   ├── buyers.py        # Buyer auth, profile, orders & requirements endpoints
│   │   ├── crops.py         # Marketplace listing, filtering & CRUD endpoints
│   │   ├── orders.py        # Order placement, transportation & status updates
│   │   ├── requirements.py  # Buyer custom requests & farmer responses
│   │   └── transportation.py# Transport rates & estimation calculations
│   └── requirements.txt     # Python backend dependencies
├── frontend/
│   ├── index.html           # Home page with surplus banner and agricultural info
│   ├── farmer-login.html    # Separate farmer login & registration page
│   ├── buyer-login.html     # Separate buyer login & registration page
│   ├── farmer-dashboard.html# Farmer crop management, orders & earnings dashboard
│   ├── buyer-dashboard.html # Buyer browsing, orders, tracking & requirement requests
│   ├── marketplace.html     # Dedicated marketplace with price comparison & Buy Now
│   ├── style.css            # Green-and-white agricultural CSS theme
│   └── script.js            # Shared client API helpers, session & modal management
├── tests/
│   └── test_api.py          # Automated end-to-end API test suite (9 test cases)
├── uploads/                 # Storage directory for crop image assets
├── Dockerfile               # Container build instructions
├── docker-compose.yml       # Multi-container orchestration
├── .env.example             # Example environment configuration
├── .gitignore               # Ignored files for version control
└── README.md                # Comprehensive documentation
```

---

## 🚀 Beginner Step-by-Step Guide (Running on Windows)

### Prerequisites

1. **Python 3.8 or higher**:
   - Download from [python.org](https://www.python.org/downloads/).
   - ⚠️ **Important during installation**: Check the box **"Add Python to PATH"**.
2. **Visual Studio Code (VS Code)**:
   - Download from [code.visualstudio.com](https://code.visualstudio.com/).

---

### Step 1: Extract the Project ZIP File

1. Locate the downloaded file `AgriFlow-Complete-Project.zip`.
2. Right-click the ZIP file and select **"Extract All..."**.
3. Choose a folder on your computer (e.g., `C:\Users\YourName\Projects\AgriFlow`) and click **Extract**.

---

### Step 2: Open Project in VS Code

1. Open **Visual Studio Code**.
2. Click **File** > **Open Folder...** (or press `Ctrl + K, Ctrl + O`).
3. Select the extracted `AgriFlow` folder and click **Select Folder**.

---

### Step 3: Open Terminal in VS Code

1. In VS Code, open the integrated terminal by pressing:
   `Ctrl + ~` (tilde key) or clicking **Terminal** > **New Terminal** from the top menu.

---

### Step 4: Install Dependencies

In the VS Code terminal, run:

```powershell
python -m pip install -r backend/requirements.txt
```

*(This installs `fastapi`, `uvicorn`, `pydantic`, `python-multipart`, and `requests`)*.

---

### Step 5: Start the AgriFlow Application

Run the following command in the terminal:

```powershell
python backend/main.py
```

You will see:
```text
==================================================================
   Starting AgriFlow – Agricultural Marketplace Server
   Open your browser at: http://127.0.0.1:8000
   Interactive Swagger API Docs: http://127.0.0.1:8000/docs
==================================================================
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

---

### Step 6: Open the Website in Your Browser

Open Google Chrome, Microsoft Edge, or Firefox and go to:

👉 **[http://127.0.0.1:8000](http://127.0.0.1:8000)**

The AgriFlow website is now live! The backend automatically serves the frontend HTML, handles all API requests, and stores data in a persistent local SQLite database (`backend/agriflow.db`).

---

## 🔑 Pre-Seeded Demo Accounts (1-Click Testing)

The database automatically seeds realistic sample data on first launch so you can test immediately without typing:

| Role | Email | Password | Details |
| :--- | :--- | :--- | :--- |
| **Farmer Demo** | `ramesh@agriflow.com` | `farmer123` | Ramesh Patel (Nashik, Maharashtra) |
| **Farmer Demo 2** | `suresh@agriflow.com` | `farmer123` | Suresh Kumar (Mandya, Karnataka) |
| **Buyer Demo** | `anita@freshmart.com` | `buyer123` | Anita Sharma (FreshMart Organics, Bangalore) |
| **Buyer Demo 2** | `rajesh@greenfoods.com` | `buyer123` | Rajesh Gupta (Gupta Wholesale Traders, Pune) |

*Tip: Both the Farmer and Buyer login pages feature a **"Fill Demo Credentials"** button for instant one-click login!*

---

## 🧪 Running Automated Tests

To verify that all APIs, order stock deductions, surplus discounts, and transportation calculations are working properly, run:

```powershell
python tests/test_api.py
```

Expected output:
```text
Ran 9 tests in 0.56s
OK
```

---

## 🐳 Running with Docker (Optional)

If you have Docker Desktop installed, you can launch the entire project with a single command:

```bash
docker compose up --build
```

Then navigate to `http://localhost:8000` in your browser.

---

## 📖 Interactive Swagger API Documentation

FastAPI provides an automatic, interactive API testing dashboard:
- **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 👨‍🌾 User Workflow Walkthrough

1. **Browse Crops**: Visit `http://127.0.0.1:8000/marketplace.html`. Filter by category (e.g., *Vegetables*, *Grains*), or view the dedicated **Surplus Deals** banner to see discounted items.
2. **Buy as a Buyer**:
   - Click **Buy Now** on any crop card.
   - Enter desired quantity in kg.
   - Select **Yes, I need transportation** and choose a vehicle (e.g. *Mini Truck*).
   - Enter your distance in km. Notice how the price breakdown instantly updates:
     $$\text{Crop Quantity} \times \text{Price} + \text{Transportation} = \text{Final Total}$$
   - Click **Confirm & Place Order**.
3. **Manage as a Farmer**:
   - Log in as the Farmer (`ramesh@agriflow.com`).
   - The Farmer Dashboard shows the incoming order with the requested delivery and transport details.
   - Click **Accept** or change status to **Dispatched** or **Delivered**.
   - View your total listed stock and estimated earnings automatically update!
4. **Post Custom Crop Requirement**:
   - In Buyer Dashboard, click **+ Post Custom Crop Requirement**.
   - Fill in needed crop, target price, and delivery date.
   - Log in as Farmer, switch to **Buyer Requirement Requests**, and submit a supply quote!
