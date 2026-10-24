
import os
import random
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from pymongo import MongoClient

# Load the MongoDB connection string from main/.env
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)


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

        # Find one vehicle in MongoDB Atlas
        vehicle = vehicles.find_one()

        if vehicle is None:
            print("No vehicle found. Run generate_vehicles.py first.")
            return

        # Generate 10 simulated sensor readings
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

            readings.insert_one(reading)

        print("10 sensor readings saved successfully to MongoDB Atlas!")
        print(f"Vehicle: {vehicle['registration_number']}")
        print("Collection: simdoctor.sensor_readings")

    except Exception as error:
        print("ERROR: Could not save sensor readings.")
        print(type(error).__name__)
        print(error)

    finally:
        if client is not None:
            client.close()


if __name__ == "__main__":
    simulate_sensor_readings()
