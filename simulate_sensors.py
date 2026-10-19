import sqlite3
import random

DATABASE = "simdoctor.db"

def simulate_sensor_readings():
    connection = sqlite3.connect(DATABASE)
    cursor = connection.cursor()

    # find the first vehicle in the database
    cursor.execute("SELECT vehicle_id FROM vehicle LIMIT 1")
    vehicle = cursor.fetchone()

    if vehicle is None:
        print("No vehicle found. run test_database.py first.")
        connection.close()
        return

    vehicle_id = vehicle[0]

    # generate 10 simulated sensor readings
    for second in range(10):
        temperature = round(random.uniform(85, 105), 2)
        voltage = round(random.uniform(12.0, 14.5), 2)
        speed = round(random.uniform(0, 100), 2)    

        cursor.execute("""
        INSERT INTO sensor_readings (vehicle_id, time_seconds, temperature, voltage, speed)
        VALUES (?, ?, ?, ?, ?)
        """, (
            vehicle_id,
            second,
            temperature,
            voltage,
            speed
        ))

    connection.commit()
    connection.close()

    print("10 sensor readings saved successfuly")

if __name__ == "__main__":
    simulate_sensor_readings()
    