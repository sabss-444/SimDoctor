
import os
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv
from pymongo import MongoClient, UpdateOne
import json 

# Load the existing MongoDB connection settings
load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")

if not MONGODB_URI:
    raise ValueError("MONGODB_URI is missing from your .env file.")

client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=10000)
db = client["simdoctor"]
knowledge = db["diagnostic_knowledge"]

documents = [
    {
        "topic": "engine_overheating",
        "fault_code": "ENGINE_OVERHEAT",
        "title": "Engine overheating",
        "symptoms": [
            "Engine temperature above the configured threshold",
            "Temperature continuing to rise",
            "steam coming from under the bonnet",
            "temperature gauge in the red or climbing high",
            "engine feels very hot and there is hot smell"
        ],
        "possible_causes": [
            "Low coolant level",
            "Cooling system leak",
            "Cooling fan malfunction",
            "Faulty temperature sensor"
        ],
        "recommended_checks": [
            "Check coolant level when safe and the engine is cool",
            "Inspect the cooling system for leaks",
            "Check cooling fan operation",
            "Verify the temperature sensor reading"
        ],
        "severity": "high",
        "keywords": ["overheating", "hot engine", "coolant", "temperature", "steam", "engine too hot", "gauge in the red", "car running hot"]
    },
    {
        "topic": "low_battery_voltage",
        "fault_code": "LOW_BATTERY_VOLTAGE",
        "title": "Low battery voltage",
        "symptoms": [
            "Battery voltage below the configured threshold",
            "Possible difficulty starting or electrical issues",
            "car struggling or slow to start",
            "headlights and dashboard look dim",
            "battery warning light on"
        ],
        "possible_causes": [
            "Discharged or worn battery",
            "Charging system problem",
            "Loose or corroded electrical connections"
        ],
        "recommended_checks": [
            "Measure battery voltage using an appropriate procedure",
            "Inspect battery terminals and connections",
            "Check the charging system"
        ],
        "severity": "medium",
        "keywords": ["battery", "low voltage", "charging", "electrical", "dead battery", "slow to start", "battery light", "flat battery"]
    },
    {
        "topic": "low_oil_pressure",
        "fault_code": "LOW_OIL_PRESSURE",
        "title": "Low oil pressure",
        "symptoms": [
            "Oil pressure below the configured threshold",
            "red oil can warning light on the dashboard",
            "ticking or knocking noise from the engine",
            "oil warning light flickering"
        ],
        "possible_causes": [
            "Low engine oil level",
            "Lubrication system problem",
            "Oil pump issue",
            "Faulty pressure sensor"
        ],
        "recommended_checks": [
            "Stop the engine if a real low-oil-pressure warning occurs",
            "Check the oil level according to the vehicle manual",
            "Investigate the lubrication system and sensor"
        ],
        "severity": "high",
        "keywords": ["oil", "pressure", "lubrication", "engine", "oil light", "engine knocking", "oil can warning", "low oil pressure"]
    }
]

documents += json.loads((Path(__file__).parent / "knowledge_data.json").read_text(encoding="utf-8"))

operations = []

for document in documents:
    document["updated_at"] = datetime.now(timezone.utc)

    operations.append(
        UpdateOne(
            {"topic": document["topic"]},
            {"$set": document},
            upsert=True
        )
    )

try:
    client.admin.command("ping")

    result = knowledge.bulk_write(operations)

    print("Diagnostic knowledge seeded successfully!")
    print(f"Documents added: {result.upserted_count}")
    print(f"Documents updated: {result.modified_count}")
    print(f"Total knowledge documents: {knowledge.count_documents({})}")

finally:
    client.close()
