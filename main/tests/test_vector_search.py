
from pathlib import Path
from dotenv import load_dotenv
from pymongo import MongoClient
import os

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

uri = os.getenv("MONGODB_URI")
if not uri:
    raise ValueError("MONGODB_URI was not found in .env")

client = MongoClient(uri)

try:
    db = client["simdoctor"]
    knowledge = db["diagnostic_knowledge"]

    question = "My engine is getting too hot. What could be wrong?"

    pipeline = [
        {
            "$vectorSearch": {
                "index": "simdoctor_knowledge_vector_index",
                "path": "search_text",
                "query": question,
                "numCandidates": 10,
                "limit": 3
            }
        },
        {
            "$project": {
                "_id": 0,
                "title": 1,
                "fault_code": 1,
                "severity": 1,
                "possible_causes": 1,
                "score": {"$meta": "vectorSearchScore"}
            }
        }
    ]

    results = list(knowledge.aggregate(pipeline))

    print(f"Question: {question}\n")

    if not results:
        print("No results returned. Check the index status and configuration.")
    else:
        for result in results:
            print(f"Diagnosis: {result.get('title')}")
            print(f"Fault code: {result.get('fault_code')}")
            print(f"Severity: {result.get('severity')}")
            print(f"Similarity score: {result.get('score')}")
            print(f"Possible causes: {result.get('possible_causes')}")
            print("-" * 50)

finally:
    client.close()
