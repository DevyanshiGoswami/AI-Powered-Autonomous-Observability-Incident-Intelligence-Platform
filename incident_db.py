import sqlite3

# -------------------------
# CREATE DATABASE
# -------------------------
conn = sqlite3.connect("incidents.db")

cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS incidents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    service TEXT,
    risk REAL,
    causes TEXT
)
""")

conn.commit()

print("✅ Incident database ready")