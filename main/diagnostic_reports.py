import os
from pathlib import Path
from dotenv import load_dotenv
from pymongo import MongoClient
from datetime import datetime, timezone

env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

DIAGNOSTIC_GUIDANCE = {
    "ENGINE_OVERHEAT": {
        "severity": "high",
        "possible_cause": (
            "the engine temperature is above the configurd "
            "simulation threshold. A cooling system issue is one "
            "possible expanation."
        ),
        "reccomended_action": (
            "If this were a real vehicle, stop safely if overheating "
            "is iindicatd, switch off the engine when safe, allow it "
            "to cool,and arrange an appropiate inspection. "
            "Never open a hot pressurised coolant cap."
        ),
    },
    "LOW_BATTERY_VOLTAGE": {
        "severity": "medium",
        "possible_cause": (
            "The measured voltage is below the configured simulation "
            "threshold. Possible explanations include a low battery "
            "charge or a charging-system issue."
        ),
        "recommended_action": (
            "Check the vehicle-specific voltage specification and "
            "have the battery and charging system tested."
        ),
    },
    "LOW_OIL_PRESSURE": {
        "severity": "high",
        "possible_cause": (
            "The measured oil pressure is below the configured "
            "simulation threshold. Possible explanations include "
            "low oil level or an oil-pressure system issue."
        ),
        "recommended_action": (
            "If this were a real vehicle, stop the engine safely "
            "as soon as possible and seek qualified assistance. "
            "Check the manufacturer's guidance before restarting."
        ),
    },
}

def build_report(fault):
    """Turn a detected fault into a structured diagnostic report."""
    code = fault.get("code", "UNKNOWN_FAULT")

    guidance = DIAGNOSTIC_GUIDANCE.get(
        code,
        {
            "severity": "unknown",
            "possible_cause": (
                "The system detected an unusual sensor reading, "
                "but no specific guidance is configured for this fault."
            ),
            "recommended_action": (
                "Review the sensor reading and consult the "
                "vehicle-specific service information."
            ),
        },
    )

    return {
        "fault_code": code,
        "message": fault.get("message", "Unspecified fault"),
        "sensor_field": fault.get("field"),
        "observed_value": fault.get("value"),
        "threshold": fault.get("threshold"),
        "unit": fault.get("unit"),
        "severity": guidance["severity"],
        "possible_cause": guidance["possible_cause"],
        "recommended_action": guidance["recommended_action"],
        "registration_number": fault.get("registration_number"),
        "vehicle_id": fault.get("vehicle_id"),
        "reading_id": fault.get("reading_id"),
        "fault_detected_at": fault.get("detected_at"),
        "status": "open",
        "report_type": "rule_based_simulation",
    }


def generate_reports():
    """Read faults from Atlas and create or update their reports."""
    client = None

    try:
        uri = os.getenv("MONGODB_URI")

        if not uri:
            print("ERROR: MONGODB_URI was not found in main/.env")
            return

        client = MongoClient(uri, serverSelectionTimeoutMS=10000)
        client.admin.command("ping")
        print("Connected successfully to MongoDB Atlas.")

        db = client["simdoctor"]
        faults_collection = db["faults"]
        reports_collection = db["diagnostic_reports"]

        faults = list(faults_collection.find())
        if not faults:
            print("No detected faults found. Run the sensor simulator first.")
            return

        new_reports = 0

        for fault in faults:
            report = build_report(fault)

            # One report per fault record; preserve its original creation time
            # and current status if this script is run again.
            fault_id = fault["_id"]
            report["fault_id"] = fault_id

            now = datetime.now(timezone.utc)

            result = reports_collection.update_one(
                {"fault_id": fault_id},
                {
                    "$set": report,
                    "$setOnInsert": {
                        "created_at": now,
                    },
                },
                upsert=True,
            )

            if result.upserted_id is not None:
                new_reports += 1

            print(
                f"[{report['severity'].upper()}] "
                f"{report['fault_code']} | "
                f"{report['registration_number'] or 'Unknown vehicle'}"
            )
            print(f"  Possible cause: {report['possible_cause']}")
            print(f"  Recommended action: {report['recommended_action']}")
            print()

        print(f"Fault records processed: {len(faults)}")
        print(f"New reports created: {new_reports}")
        print("Reports saved in: simdoctor.diagnostic_reports")

    except Exception as error:
        print("ERROR: Could not generate diagnostic reports.")
        print(type(error).__name__)
        print(error)

    finally:
        if client is not None:
            client.close()


if __name__ == "__main__":
    generate_reports()
