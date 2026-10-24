
"""
fault_detector.py - rule-based fault detection for SimDoctor.

Thresholds are for simulation only, not universal vehicle diagnostics.
"""

import os
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from pymongo import MongoClient


RULES = [
    {
        "code": "ENGINE_OVERHEAT",
        "field": "temperature",
        "operator": ">",
        "threshold": 105.0,
        "unit": "°C",
        "message": "Possible overheating",
    },
    {
        "code": "LOW_BATTERY_VOLTAGE",
        "field": "voltage",
        "operator": "<",
        "threshold": 12.0,
        "unit": "V",
        "message": "Possible low-voltage issue",
    },
    {
        "code": "LOW_OIL_PRESSURE",
        "field": "oil_pressure",
        "operator": "<",
        "threshold": 1.0,
        "unit": "bar",
        "message": "Possible low oil pressure",
    },
]

OPERATORS = {
    ">": lambda value, limit: value > limit,
    "<": lambda value, limit: value < limit,
}


def detect_faults(reading, rules=RULES):
    """Return a list of faults detected in one sensor reading."""
    faults = []

    for rule in rules:
        value = reading.get(rule["field"])

        # Ignore missing, non-numeric, and boolean values.
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            continue

        if OPERATORS[rule["operator"]](value, rule["threshold"]):
            faults.append({
                "code": rule["code"],
                "message": rule["message"],
                "field": rule["field"],
                "value": value,
                "operator": rule["operator"],
                "threshold": rule["threshold"],
                "unit": rule["unit"],
                "detected_at": datetime.now(timezone.utc).isoformat(),
            })

    return faults


def describe(fault):
    """Format a fault as a readable message."""
    direction = "above" if fault["operator"] == ">" else "below"

    return (
        f"[{fault['code']}] {fault['message']}: "
        f"{fault['field']} = {fault['value']} {fault['unit']} "
        f"({direction} limit of "
        f"{fault['threshold']} {fault['unit']})"
    )


def save_fault(fault_log, reading, fault):
    """Save a fault once per sensor reading and fault code."""
    fault_document = {
        **fault,
        "reading_id": reading["_id"],
        "vehicle_id": reading.get("vehicle_id"),
        "registration_number": reading.get("registration_number"),
    }

    # Keep the original detected_at when this fault already exists.
    detected_at = fault_document.pop("detected_at")

    result = fault_log.update_one(
        {
            "reading_id": reading["_id"],
            "code": fault["code"],
        },
        {
            "$set": fault_document,
            "$setOnInsert": {"detected_at": detected_at},
        },
        upsert=True,
    )

    return result.upserted_id is not None


def scan_mongodb(limit=50):
    """Scan recent sensor readings and store detected faults."""
    env_path = Path(__file__).parent / ".env"
    load_dotenv(env_path)

    uri = os.getenv("MONGODB_URI")

    if not uri:
        raise SystemExit("MONGODB_URI not found in main/.env")

    client = MongoClient(uri, serverSelectionTimeoutMS=10000)

    try:
        client.admin.command("ping")
        print("Connected successfully to MongoDB Atlas.")

        db = client["simdoctor"]
        readings = db["sensor_readings"]
        fault_log = db["faults"]

        scanned = 0
        detections = 0
        new_faults = 0

        for reading in (
            readings.find()
            .sort("timestamp", -1)
            .limit(limit)
        ):
            scanned += 1

            for fault in detect_faults(reading):
                detections += 1
                is_new = save_fault(fault_log, reading, fault)

                if is_new:
                    new_faults += 1

                registration = reading.get("registration_number", "?")
                print(f"{registration} | {describe(fault)}")

        print(f"\nReadings scanned: {scanned}")
        print(f"Fault detections processed: {detections}")
        print(f"New fault records inserted: {new_faults}")
        print("Fault collection: simdoctor.faults")

    finally:
        client.close()


if __name__ == "__main__":
    scan_mongodb()
