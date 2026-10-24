
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
                "_id": "$vehicle_id",
                "total_faults": {"$sum": 1},
                "fault_codes": {"$addToSet": "$code"}
            }
        },
        {
            "$lookup": {
                "from": "diagnostic_reports",
                "localField": "_id",
                "foreignField": "vehicle_id",
                "as": "reports"
            }
        },
        {
            "$project": {
                "_id": 0,
                "vehicle_id": "$_id",
                "total_faults": 1,
                "fault_codes": 1,
                "high_severity_reports": {
                    "$size": {
                        "$filter": {
                            "input": "$reports",
                            "as": "report",
                            "cond": {
                                "$eq": ["$$report.severity", "high"]
                            }
                        }
                    }
                }
            }
        },
        {"$sort": {"total_faults": -1}}
    ]

    results = list(db["faults"].aggregate(pipeline))

    if not results:
        print("No fault records found. Run the simulator first.")
    else:
        print("SIMDOCTOR — VEHICLE FAULT SUMMARY")
        print("=" * 40)

        for result in results:
            print(f"\nVehicle ID: {result['vehicle_id']}")
            print(f"Total fault records: {result['total_faults']}")
            print(f"Fault codes: {result['fault_codes']}")
            print(
                "High-severity reports: "
                f"{result['high_severity_reports']}"
            )

finally:
    client.close()
