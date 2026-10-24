
"""
simulate_sensors.py - generate simulated sensor readings for SimDoctor.
"""

import os
import random
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from pymongo import MongoClient

from fault_detector import detect_faults, describe, save_fault


env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

FAULT_PROBABILITY = 0.25


def inject_fault(reading):
    """Inject one simulated sensor fault into a reading."""
    fault_type = random.choice([
        "overheat",
        "low_voltage",
        "low_oil",
    ])

    if fault_type == "overheat":
        reading["temperature"] = round(random.uniform(106, 125), 2)

    elif fault_type == "low_voltage":
        reading["voltage"] = round(random.uniform(10.0, 11.9), 2)

    else:
        reading["oil_pressure"] = round(random.uniform(0.2, 0.9), 2)

    return reading


def simulate_sensor_readings():
    uri = os.getenv("MONGODB_URI")

    if not uri:
        print("ERROR: MONGODB_URI was not found in main/.env")
        return

    client = None

    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=10000)
        client.admin.command("ping")

        db = client["simdoctor"]
        vehicles = db["vehicles"]
        readings = db["sensor_readings"]
        fault_log = db["faults"]

        vehicle = vehicles.find_one()

        if vehicle is None:
            print("No vehicle found. Run generate_vehicles.py first.")
            return

        fault_count = 0

        for second in range(10):
            reading = {
                "vehicle_id": vehicle["_id"],
                "registration_number": vehicle["registration_number"],
                "timestamp": datetime.now(timezone.utc),
                "time_seconds": second,
                "temperature": round(random.uniform(85, 105), 2),
                "voltage": round(random.uniform(12.0, 14.5), 2),
                "speed": round(random.uniform(0, 100), 2),
                "rpm": random.randint(800, 6000),
                "oil_pressure": round(random.uniform(1.0, 5.0), 2),
            }

            # Randomly introduce a fault in some readings.
            if random.random() < FAULT_PROBABILITY:
                inject_fault(reading)

            # Save the reading and obtain its MongoDB ID.
            result = readings.insert_one(reading)
            reading["_id"] = result.inserted_id

            # Detect and save any faults found in this reading.
            for fault in detect_faults(reading):
                fault_count += 1
                save_fault(fault_log, reading, fault)
                print(f"t={second}s | {describe(fault)}")

        print("\nSensor simulation completed successfully!")
        print("Readings generated: 10")
        print(f"Vehicle: {vehicle['registration_number']}")
        print("Readings collection: simdoctor.sensor_readings")
        print(f"Faults detected in this run: {fault_count}")
        print("Fault collection: simdoctor.faults")

    except Exception as error:
        print("ERROR: Could not complete the simulation.")
        print(type(error).__name__)
        print(error)

    finally:
        if client is not None:
            client.close()


if __name__ == "__main__":
    simulate_sensor_readings()
