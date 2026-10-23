
import sqlite3

connection = sqlite3.connect("simdoctor.db")
cursor = connection.cursor()

cursor.execute("""
    SELECT
        v.make,
        v.model,
        s.time_seconds,
        s.temperature,
        s.voltage,
        s.speed
    FROM sensor_readings AS s
    JOIN vehicles AS v
        ON s.vehicle_id = v.vehicle_id
    ORDER BY s.reading_id DESC
    LIMIT 10
""")

readings = cursor.fetchall()

print("SIMDOCTOR SENSOR READINGS")

for reading in readings:
    print(reading)

connection.close()
