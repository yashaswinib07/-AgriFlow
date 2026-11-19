import os
import sqlite3
from typing import Generator

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_FILE = os.path.join(BASE_DIR, "agriflow.db")


def get_db_connection() -> sqlite3.Connection:
    """Create and return a new SQLite connection with Row mapping and foreign keys enabled."""
    conn = sqlite3.connect(DATABASE_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def get_db() -> Generator[sqlite3.Connection, None, None]:
    """FastAPI dependency yielding a thread-safe database connection."""
    conn = get_db_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """Create all required SQLite tables and indexes."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Farmers table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS farmers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        phone TEXT NOT NULL,
        password_hash TEXT NOT NULL,
        location TEXT NOT NULL,
        created_at TEXT NOT NULL
    );
    """)

    # 2. Buyers table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS buyers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        phone TEXT NOT NULL,
        password_hash TEXT NOT NULL,
        business_name TEXT,
        location TEXT NOT NULL,
        created_at TEXT NOT NULL
    );
    """)

    # 3. Crops table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS crops (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        farmer_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        image_url TEXT,
        description TEXT,
        quantity_kg REAL NOT NULL,
        price_per_kg REAL NOT NULL,
        discount_price_per_kg REAL,
        quality TEXT NOT NULL,
        crop_type TEXT DEFAULT 'fresh',
        harvest_date TEXT NOT NULL,
        location TEXT NOT NULL,
        is_active INTEGER DEFAULT 1,
        created_at TEXT NOT NULL,
        FOREIGN KEY (farmer_id) REFERENCES farmers(id) ON DELETE CASCADE
    );
    """)

    # 4. Orders table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        buyer_id INTEGER NOT NULL,
        farmer_id INTEGER NOT NULL,
        crop_id INTEGER NOT NULL,
        quantity_kg REAL NOT NULL,
        price_per_kg REAL NOT NULL,
        crop_amount REAL NOT NULL,
        requires_transport INTEGER DEFAULT 0,
        vehicle_type TEXT,
        delivery_location TEXT NOT NULL,
        distance_km REAL DEFAULT 0.0,
        transport_charge REAL DEFAULT 0.0,
        final_amount REAL NOT NULL,
        status TEXT DEFAULT 'Pending',
        notes TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY (buyer_id) REFERENCES buyers(id),
        FOREIGN KEY (farmer_id) REFERENCES farmers(id),
        FOREIGN KEY (crop_id) REFERENCES crops(id)
    );
    """)

    # 5. Buyer Requirements table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS buyer_requirements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        buyer_id INTEGER NOT NULL,
        crop_name TEXT NOT NULL,
        category TEXT NOT NULL,
        quantity_kg REAL NOT NULL,
        expected_price_per_kg REAL NOT NULL,
        delivery_location TEXT NOT NULL,
        required_date TEXT NOT NULL,
        requires_transport INTEGER DEFAULT 0,
        description TEXT,
        status TEXT DEFAULT 'Open',
        created_at TEXT NOT NULL,
        FOREIGN KEY (buyer_id) REFERENCES buyers(id) ON DELETE CASCADE
    );
    """)

    # 6. Requirement Responses table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS requirement_responses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        requirement_id INTEGER NOT NULL,
        farmer_id INTEGER NOT NULL,
        offered_price_per_kg REAL NOT NULL,
        available_quantity_kg REAL NOT NULL,
        message TEXT,
        status TEXT DEFAULT 'Pending',
        created_at TEXT NOT NULL,
        FOREIGN KEY (requirement_id) REFERENCES buyer_requirements(id) ON DELETE CASCADE,
        FOREIGN KEY (farmer_id) REFERENCES farmers(id)
    );
    """)

    # 7. Transportation Rates table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transportation_rates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vehicle_type TEXT UNIQUE NOT NULL,
        base_fare REAL NOT NULL,
        rate_per_km REAL NOT NULL,
        max_capacity_kg REAL NOT NULL,
        description TEXT
    );
    """)

    conn.commit()
    conn.close()
