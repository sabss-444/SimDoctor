
from pathlib import Path
from dotenv import load_dotenv
from pymongo import MongoClient
import os

load_dotenv(Path(__file__).resolve().parent / ".env")

uri = os.getenv("MONGODB_URI")

if not uri:
    raise ValueError("MONGODB_URI was not found in your .env file")

client = MongoClient(uri)

try:
    db = client["simdoctor"]
    faults = db["faults"]
    knowledge = db["diagnostic_knowledge"]

    # Get the most recent detected faults
    recent_faults = list(
        faults.find().sort("detected_at", -1).limit(10)
    )

    if not recent_faults:
        print("No faults found. Run your sensor simulator first.")
    else:
        for fault in recent_faults:
            # Your fault records use the 'code' field
            fault_code = fault.get("code")

            if not fault_code:
                print("A fault record has no 'code' field.")
                continue

            diagnosis = knowledge.find_one(
                {"fault_code": fault_code},
                {"_id": 0}
            )

            print("\n" + "=" * 45)
            print(f"Detected fault: {fault_code}")

            if diagnosis:
                print(f"Diagnosis: {diagnosis['title']}")
                print(f"Severity: {diagnosis['severity']}")

                print("\nPossible causes:")
                for cause in diagnosis["possible_causes"]:
                    print(f"- {cause}")

                print("\nRecommended checks:")
                for check in diagnosis["recommended_checks"]:
                    print(f"- {check}")
            else:
                print("No matching diagnostic knowledge found.")

finally:
    client.close()
