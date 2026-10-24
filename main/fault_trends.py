
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

    pipeline = [
        {
            "$group": {
                "_id": "$code",
                "total_occurrences": {"$sum": 1},
                "affected_vehicles": {
                    "$addToSet": "$vehicle_id"
                }
            }
        },
        {
            "$project": {
                "_id": 0,
                "fault_code": "$_id",
                "total_occurrences": 1,
                "number_of_vehicles": {
                    "$size": "$affected_vehicles"
                }
            }
        },
        {
            "$sort": {
                "total_occurrences": -1
            }
        }
    ]

    results = list(db["faults"].aggregate(pipeline))

    print("SIMDOCTOR — FAULT TRENDS")
    print("=" * 35)

    if not results:
        print("No fault records found.")
    else:
        for result in results:
            print(f"\nFault: {result['fault_code']}")
            print(f"Occurrences: {result['total_occurrences']}")
            print(
                "Vehicles affected: "
                f"{result['number_of_vehicles']}"
            )

finally:
    client.close()
