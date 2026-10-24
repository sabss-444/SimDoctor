import os
from datetime import datetime, timezone
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")

if not MONGODB_URI:
    raise ValueError("MONGODB_URI not found in main/.env")

client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=10000)
db = client["simdoctor"]
knowledge = db["diagnostic_knowledge"]

documents = [
    {
        "topic": "enging_overheating",
        "fault_code": "ENGINE_OVERHEAT",
        "title": "Engine overheating",
        "symptoms": [
            "Engine temperature above the configurd threshold",
            "Temperature continuing to rise"
        ],
        "possible_causes": [
            "Low coolant level",
            "Cooling system leak",
            "Cooling fan malfunction",
            "Faulty temperature sensor"
        ],
        "recommended_checks": [
            "Check coolant level when safe and the engine is cool",
            "Inspect cooling system for leaks",
            "Check cooling fan operation",
            "verify the temperature sensor reading"
        ],
        "severity": "high",
        "keywords": ["overheating", "hot engine", "coolant", "temperature",]
    },
    {
        "Topic": "low_battery_voltage",
        "fault_code": "LOW_BATTERY_VOLTAGE",
        "title": "Low battery voltage",
        "symptoms": [
            "Measured voltage below the configurd threshold",
            "Vehicle may not start or electrical systems may fail"
        ],
        "possible_causes": [
            "Discharged or worn out battery",
            "Charging system problem",
            "Loose or corroded electrical connections"
        ],
        "recommended_checks": [
            "Check battery voltage with a multimeter",
            "Inspect battery terminals for corrosion",
            "Test alternator output",
            "Check for any parasitic draws"
        ],
        "severity": "medium",
        "keywords": ["low voltage", "battery", "electrical", "charging"]
    },
    {
        "topic": "low_oil_pressure",
        "fault_code": "LOW_OIL_PRESSURE",
        "title": "Low oil pressure",
        "symptoms": [
            "Oil pressure below the configured threshold"
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
        "keywords": ["oil", "pressure", "lubrication", "engine"]
    }
]

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