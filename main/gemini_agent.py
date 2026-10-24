import json
import os
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types
from pymongo import MongoClient

load_dotenv(Path(__file__).parent / ".env")

VECTOR_INDEX = "simdoctor_knowledge_vector_index"
MODEL = "gemini-flash-latest"

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
def ask_gemini(prompt, system=None, as_json=False):
    config = types.GenerateContentConfig(
        system_instruction=system,
        temperature=0.2,
        response_mime_type="application/json" if as_json else None,
    )
    response = client.models.generate_content(model=MODEL, contents=prompt, config=config)
    return response.text
def retrieve_knowledge(db, question, limit=3):
    pipeline = [
        {"$vectorSearch": {
            "index": VECTOR_INDEX,
            "path": "search_text",
            "query": question,
            "numCandidates": 50,
            "limit": limit,
        }},
        {"$project": {
            "_id": 0, "title": 1, "fault_code": 1, "severity": 1,
            "symptoms": 1, "possible_causes": 1, "recommended_checks": 1,
            "score": {"$meta": "vectorSearchScore"},
        }},
    ]
    return list(db["diagnostic_knowledge"].aggregate(pipeline))

if __name__ == "__main__":
    mongo = MongoClient(os.getenv("MONGODB_URI"), serverSelectionTimeoutMS=10000)
    db = mongo["simdoctor"]
    for doc in retrieve_knowledge(db, "steam coming from under my bonnet"):
        print(doc["title"], round(doc["score"], 3))
    mongo.close()
    