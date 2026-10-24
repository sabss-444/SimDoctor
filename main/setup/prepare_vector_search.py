
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
    knowledge = db["diagnostic_knowledge"]

    updated = 0

    for doc in knowledge.find():
        search_text = "\n".join([
            f"Title: {doc.get('title', '')}",
            f"Symptoms: {', '.join(doc.get('symptoms', []))}",
            f"Keywords: {', '.join(doc.get('keywords', []))}",
            f"Possible causes: {', '.join(doc.get('possible_causes', []))}",
            f"Recommended checks: {', '.join(doc.get('recommended_checks', []))}",
        ])

        knowledge.update_one(
            {"_id": doc["_id"]},
            {"$set": {"search_text": search_text}}
        )
        updated += 1

    print(f"Prepared {updated} diagnostic knowledge documents.")

    example = knowledge.find_one(
        {},
        {"_id": 0, "title": 1, "search_text": 1}
    )
    print("\nExample document:")
    print(example)

finally:
    client.close()
