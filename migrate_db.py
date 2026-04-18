"""
migrate_db.py — Safely add E-Challan columns to existing traffic_system.db
Run once before starting the server: python migrate_db.py
"""
import sqlite3
import os

DB_PATH = "./database/traffic_system.db"

def column_exists(cursor, table, column):
    cursor.execute(f"PRAGMA table_info({table})")
    return any(row[1] == column for row in cursor.fetchall())

def migrate():
    if not os.path.exists(DB_PATH):
        print(f"DB not found at {DB_PATH} — will be created fresh by the app.")
        return

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # ── violations table: add E-Challan columns ──────────────────────────────
    new_columns = [
        ("challan_number",   "TEXT"),
        ("payment_status",   "TEXT DEFAULT 'Pending'"),
        ("payment_date",     "DATETIME"),
        ("challan_pdf_path", "TEXT"),
    ]
    for col, col_type in new_columns:
        if not column_exists(cur, "violations", col):
            cur.execute(f"ALTER TABLE violations ADD COLUMN {col} {col_type}")
            print(f"  [OK]  Added column `violations.{col}`")
        else:
            print(f"  [SKIP]  Column `violations.{col}` already exists")

    # ── Fix any NULL payment_status → 'Pending' ──────────────────────────────
    cur.execute("UPDATE violations SET payment_status = 'Pending' WHERE payment_status IS NULL")
    fixed = cur.rowcount
    if fixed:
        print(f"  [FIX]  Set payment_status='Pending' for {fixed} existing row(s)")

    # ── vehicle_owners table (mock owner lookup) ──────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS vehicle_owners (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            plate_number TEXT UNIQUE NOT NULL,
            owner_name  TEXT,
            email       TEXT,
            phone       TEXT DEFAULT 'N/A',
            address     TEXT DEFAULT 'Smart City, India'
        )
    """)
    print("  [OK]  `vehicle_owners` table ready")

    # ── system_settings table (Control Room) ─────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS system_settings (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            location_name     TEXT DEFAULT 'Main Junction - Signal 01',
            camera_source     TEXT DEFAULT 'videos/traffic_demo.mp4',
            input_mode        TEXT DEFAULT 'VIDEO',
            speed_limit       REAL DEFAULT 50.0,
            distance_meters   REAL DEFAULT 5.0,
            presentation_mode INTEGER DEFAULT 1,
            helmet_detection  INTEGER DEFAULT 1,
            lane_detection    INTEGER DEFAULT 1,
            updated_at        DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("  [OK]  `system_settings` table ready")

    # ── Check if new columns exist in system_settings if it was already created ──
    for col in ["helmet_detection", "lane_detection"]:
        if not column_exists(cur, "system_settings", col):
            cur.execute(f"ALTER TABLE system_settings ADD COLUMN {col} INTEGER DEFAULT 1")
            print(f"  [OK]  Added missing column `system_settings.{col}`")

    conn.commit()
    conn.close()
    print("\nMigration complete! You can now start the server.")

if __name__ == "__main__":
    migrate()
