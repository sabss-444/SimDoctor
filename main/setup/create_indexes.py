"""Create (or verify) every Atlas index SimDoctor needs.

Run from the main/ folder:   python setup/create_indexes.py
Safe to re-run: existing indexes are left alone.

Indexes
  1. simdoctor_knowledge_vector_index  Atlas Vector Search + Automated Embedding (Voyage AI)
  2. simdoctor_knowledge_text          Atlas Search (lexical / full-text)

Both read the `search_text` field that setup/prepare_vector_search.py builds.
Indexes build asynchronously: wait until status is READY (about 1-3 minutes).
"""
import os
from pathlib import Path

from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.operations import SearchIndexModel

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

URI = os.getenv("MONGODB_URI")
if not URI:
    raise SystemExit("MONGODB_URI missing from main/.env")

DB_NAME = "simdoctor"
COLLECTION = "diagnostic_knowledge"

VECTOR_INDEX = "simdoctor_knowledge_vector_index"
TEXT_INDEX = "simdoctor_knowledge_text"
EMBED_MODEL = os.getenv("EMBED_MODEL", "voyage-4")   # voyage-4-lite is cheaper/faster

VECTOR_DEFINITION = {
    "fields": [
        {"type": "autoEmbed", "modality": "text", "path": "search_text", "model": EMBED_MODEL},
        {"type": "filter", "path": "fault_code"},
        {"type": "filter", "path": "severity"},
    ]
}

TEXT_DEFINITION = {
    "mappings": {
        "dynamic": False,
        "fields": {
            "title": {"type": "string"},
            "search_text": {"type": "string"},
            "keywords": {"type": "string"},
            "symptoms": {"type": "string"},
            "possible_causes": {"type": "string"},
            "fault_code": {"type": "token"},
            "severity": {"type": "token"},
        },
    }
}


def ensure(collection, name, definition, index_type):
    existing = {i["name"]: i for i in collection.list_search_indexes()}
    if name in existing:
        print(f"[skip]    {name} already exists (status: {existing[name].get('status')})")
        return
    collection.create_search_index(SearchIndexModel(definition=definition, name=name, type=index_type))
    print(f"[created] {name} ({index_type})")


def main():
    client = MongoClient(URI, serverSelectionTimeoutMS=15000)
    try:
        collection = client[DB_NAME][COLLECTION]
        print(f"Connected. Server version: {client.server_info().get('version')}")
        print(f"{COLLECTION}: {collection.count_documents({})} documents")
        if collection.count_documents({"search_text": {"$exists": True}}) == 0:
            print("WARNING: no search_text field found. Run setup/prepare_vector_search.py first.")
        ensure(collection, VECTOR_INDEX, VECTOR_DEFINITION, "vectorSearch")
        ensure(collection, TEXT_INDEX, TEXT_DEFINITION, "search")
        print("\nCheck status in Atlas > Search & Vector Search. Wait for READY before querying.")
    finally:
        client.close()


if __name__ == "__main__":
    main()
    