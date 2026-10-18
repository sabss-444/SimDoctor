import sqlite3

connection = sqlite3.connect("simdoctor.db")
connection.execute("PRAGMA foreign_keys = ON")
cursor = connection.cursor()

cursor.execute("SELECT vehicle_id FROM vehicles LIMIT 1")
vehicle = cursor.fetchone()

if vehicle is None:
    print("Add a vehicle before migrating sensor readings.")
else:
    cursor.execute("PRAGMA table_info(sensor_readings)")
    columns = [row[1] for row in cursor.fetchall()]

    if "vehicle_id" not in columns:
        cursor.execute("""
        CREATE TABLE sensor_readings_new (
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

        cursor.execute("""
        INSERT INTO sensor_readings_new
        (reading_id, vehicle_id, time_seconds, temperature, voltage, speed, created_at)
        SELECT
            reading_id, ?, time_seconds, temperature, voltage, speed, created_at
        FROM sensor_readings
        """, (vehicle[0],))

        cursor.execute("DROP TABLE sensor_readings")
        cursor.execute("ALTER TABLE sensor_readings_new RENAME TO sensor_readings")

        connection.commit()
        print("Migration completed.")
    else:
        print("Sensor table already has vehicle_id.")

connection.close()
