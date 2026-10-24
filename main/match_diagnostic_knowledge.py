
from pathlib import Path
from dotenv import load_dotenv
from pymongo import MongoClient
import os

load_dotenv(Path(__file__).resolve().parent / ".env")

client = MongoClient(os.getenv("MONGODB_URI"))

try:
    db = client["simdoctor"]
    knowledge = db["diagnostic_knowledge"]

    # Example: pretend the simulator detected an overheating fault
    detected_fault_code = "ENGINE_OVERHEAT"

    result = knowledge.find_one(
        {"fault_code": detected_fault_code},
        {"_id": 0}
    )

    if result:
        print(f"DIAGNOSIS: {result['title']}")
        print(f"Severity: {result['severity']}")

        print("\nPossible causes:")
        for cause in result["possible_causes"]:
            print(f"- {cause}")

        print("\nRecommended checks:")
        for check in result["recommended_checks"]:
            print(f"- {check}")
    else:
        print(f"No diagnostic knowledge found for {detected_fault_code}")

finally:
    client.close()
