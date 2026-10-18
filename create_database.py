
import sqlite3

# Connect to the existing database
connection = sqlite3.connect("simdoctor.db")

# Enable foreign key relationships
connection.execute("PRAGMA foreign_keys = ON")

cursor = connection.cursor()

# 1. Store vehicle information
cursor.execute("""
CREATE TABLE IF NOT EXISTS vehicles (
    vehicle_id INTEGER PRIMARY KEY AUTOINCREMENT,
    make TEXT,
    model TEXT,
    year INTEGER,
    mileage INTEGER
)
""")

# 2. Store chatbot conversations
cursor.execute("""
CREATE TABLE IF NOT EXISTS conversations (
    conversation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    vehicle_id INTEGER,
    user_message TEXT NOT NULL,
    ai_response TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (vehicle_id)
        REFERENCES vehicles(vehicle_id)
)
""")

# 3. Store diagnostic reports
cursor.execute("""
CREATE TABLE IF NOT EXISTS diagnostic_reports (
    report_id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER,
    suspected_cause TEXT,
    evidence TEXT,
    urgency TEXT,
    recommendation TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id)
        REFERENCES conversations(conversation_id)
)
""")

# 4. Store simulated sensor readings
cursor.execute("""
CREATE TABLE IF NOT EXISTS sensor_readings (
    reading_id INTEGER PRIMARY KEY AUTOINCREMENT,
    vehicle_id INTEGER NOT NULL,
    time_seconds INTEGER NOT NULL,
    temperature REAL,
    voltage REAL,
    speed REAL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (vehicle_id)
        REFERENCES vehicles(vehicle_id)
)
""")

connection.commit()
connection.close()

print("SimDoctor database setup complete!")

