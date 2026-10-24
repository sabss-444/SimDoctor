
from pathlib import Path
from dotenv import load_dotenv
from pymongo import MongoClient
import os

load_dotenv(Path(__file__).resolve().parent / ".env")

uri = os.getenv("MONGODB_URI")
if not uri:
    raise ValueError("MONGODB_URI was not found in .env")

client = MongoClient(uri)

try:
    db = client["simdoctor"]
    readings = db["sensor_readings"]

    pipeline = [
        {
            "$group": {
                "_id": "$vehicle_id",
                "total_readings": {"$sum": 1},
                "maximum_temperature": {"$max": "$temperature"},
                "average_temperature": {"$avg": "$temperature"},
                "average_oil_pressure": {"$avg": "$oil_pressure"},
                "average_voltage": {"$avg": "$voltage"},
                "maximum_rpm": {"$max": "$rpm"}
            }
        },
        {
            "$sort": {"maximum_temperature": -1}
        },
        {
            "$project": {
                "_id": 0,
                "vehicle_id": "$_id",
                "total_readings": 1,
                "maximum_temperature": {
                    "$round": ["$maximum_temperature", 2]
                },
                "average_temperature": {
                    "$round": ["$average_temperature", 2]
                },
                "average_oil_pressure": {
                    "$round": ["$average_oil_pressure", 2]
                },
                "average_voltage": {
                    "$round": ["$average_voltage", 2]
                },
                "maximum_rpm": 1
            }
        }
    ]

    results = list(readings.aggregate(pipeline))

    if not results:
        print("No sensor readings found. Run the sensor simulator first.")
    else:
        print("SIMDOCTOR — VEHICLE HEALTH SUMMARY")
        print("=" * 45)

        for result in results:
            print(f"\nVehicle ID: {result['vehicle_id']}")
            print(f"Readings collected: {result['total_readings']}")
            print(f"Maximum temperature: {result['maximum_temperature']} °C")
            print(f"Average temperature: {result['average_temperature']} °C")
            print(f"Average oil pressure: {result['average_oil_pressure']} bar")
            print(f"Average voltage: {result['average_voltage']} V")
            print(f"Maximum RPM: {result['maximum_rpm']}")

finally:
    client.close()
