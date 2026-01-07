# db.py
# Updated version: Fixed deprecation warning for date handling in SQLite (Python 3.12+).
# Added explicit date adapters and enabled PARSE_DECLTYPES for proper date object retrieval.
# This ensures dates are stored as TEXT (ISO format) but retrieved as datetime.date objects.
# Also minor improvements: Better connection handling, added more CRUD functions for next steps.

import sqlite3
from datetime import date, datetime
import pandas as pd

# Database file name
DB_FILE = 'fleet.db'

# Register adapters globally (once per app run) to handle date/datetime properly.
# This prevents the deprecation warning and ensures correct insertion.
sqlite3.register_adapter(date, lambda d: d.isoformat())
sqlite3.register_adapter(datetime, lambda dt: dt.isoformat())

def get_connection():
    """Establishes and returns a connection with proper date parsing."""
    conn = sqlite3.connect(DB_FILE, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row  # Dict-like rows for easier access
    return conn

def create_tables():
    """Creates the database tables if they don't exist."""
    conn = get_connection()
    c = conn.cursor()
    
    # Vehicles table
    c.execute('''
    CREATE TABLE IF NOT EXISTS vehicles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        year INTEGER,
        brand TEXT,
        model TEXT,
        plate_reg TEXT,
        vin TEXT,
        status TEXT DEFAULT 'Active',
        operator TEXT,
        gasoline_type TEXT,
        tank_capacity REAL,
        location TEXT,
        acquisition_date DATE,
        exp_date DATE,
        last_updated_on DATE,
        next_service_due DATE,
        current_mileage REAL DEFAULT 0.0
    )
    ''')
    
    # Maintenance Logs
    c.execute('''
    CREATE TABLE IF NOT EXISTS maintenance_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vehicle_id INTEGER,
        date DATE,
        description TEXT,
        odometer REAL,
        service_provider TEXT,
        mechanic TEXT,
        part_no TEXT,
        next_service_due DATE,
        material_cost REAL DEFAULT 0.0,
        labor_cost REAL DEFAULT 0.0,
        warranty TEXT,
        total_cost REAL DEFAULT 0.0,
        FOREIGN KEY(vehicle_id) REFERENCES vehicles(id) ON DELETE CASCADE
    )
    ''')
    
    # Expenses (simple cost tracking)
    c.execute('''
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vehicle_id INTEGER,
        date DATE,
        description TEXT,
        cost REAL DEFAULT 0.0,
        FOREIGN KEY(vehicle_id) REFERENCES vehicles(id) ON DELETE CASCADE
    )
    ''')
    
    # Preventative Schedules (global for MVP)
    c.execute('''
    CREATE TABLE IF NOT EXISTS preventative_schedules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mileage INTEGER,
        recommended_maintenance TEXT
    )
    ''')
    
    conn.commit()
    conn.close()

def insert_sample_data():
    """Inserts sample data from the XLSX for testing."""
    conn = get_connection()
    c = conn.cursor()
    
    # Sample vehicle
    c.execute('''
    INSERT OR IGNORE INTO vehicles 
    (year, brand, model, plate_reg, vin, status, operator, gasoline_type, tank_capacity, location, acquisition_date, exp_date, last_updated_on, next_service_due, current_mileage)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (2021, 'Ford', 'Transit-350 Cargo', 'FLT012', '2T1BR18E8XC165041', 'Active', 'John Smith', 'Regular', 25.1, 'Atlanta', date(2025, 1, 1), date(2030, 1, 1), date.today(), date(2026, 4, 1), 130000))
    
    vehicle_id = c.lastrowid or 1  # Fallback if already exists
    
    # Sample maintenance logs
    c.execute('''
    INSERT INTO maintenance_logs 
    (vehicle_id, date, description, odometer, service_provider, mechanic, part_no, next_service_due, material_cost, labor_cost, total_cost)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (vehicle_id, date(2021, 6, 1), 'Oil & Filter Change', 65000, 'PepBoys', 'n/a', '5729', date(2021, 9, 1), 25, 10, 35))
    
    c.execute('''
    INSERT INTO maintenance_logs 
    (vehicle_id, date, description, odometer, service_provider, mechanic, part_no, next_service_due, material_cost, labor_cost, total_cost)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (vehicle_id, date(2021, 6, 1), 'Air Filter Change', 65000, 'PepBoys', 'n/a', '2638', date(2021, 3, 1), 10, 5, 15))
    
    # Sample preventative schedules
    schedules = [
        (10000, 'Rotate Tires, Change Oil and Filter'),
        (20000, 'Rotate Tires, Change Oil and Filter'),
        (30000, 'Replace Air Filter, Rotate Tires, Fuel Filter Replacement, Change Oil and Filter'),
        (40000, 'Rotate Tires, Change Oil and Filter'),
        (50000, 'Rotate Tires, Change Oil and Filter'),
        (60000, 'Replace Air Filter, Rotate Tires, Fuel Filter Replacement, Clean and Repack Wheel Bearing, Change Oil and Filter'),
    ]
    c.executemany('INSERT OR IGNORE INTO preventative_schedules (mileage, recommended_maintenance) VALUES (?, ?)', schedules)
    
    conn.commit()
    conn.close()

# Basic CRUD functions (expand as needed)

def get_vehicles():
    conn = get_connection()
    df = pd.read_sql_query('SELECT * FROM vehicles', conn)
    conn.close()
    return df

def add_vehicle(**kwargs):
    """Add a vehicle with keyword arguments matching table columns."""
    conn = get_connection()
    c = conn.cursor()
    columns = ', '.join(kwargs.keys())
    placeholders = ', '.join(['?' for _ in kwargs])
    c.execute(f'INSERT INTO vehicles ({columns}) VALUES ({placeholders})', tuple(kwargs.values()))
    conn.commit()
    conn.close()
    return c.lastrowid

def get_maintenance_logs(vehicle_id):
    conn = get_connection()
    df = pd.read_sql_query('SELECT * FROM maintenance_logs WHERE vehicle_id = ? ORDER BY date DESC', conn, params=(vehicle_id,))
    conn.close()
    return df

# More functions can be added here (update_vehicle, delete_vehicle, etc.)

if __name__ == '__main__':
    create_tables()
    insert_sample_data()
    print("Database initialized with sample data.")