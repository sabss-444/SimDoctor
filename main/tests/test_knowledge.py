
from pathlib import Path
from dotenv import load_dotenv
from pymongo import MongoClient
import os

# Load the .env file from the main folder
load_dotenv(Path(__file__).resolve().parent / ".env")

client = MongoClient(os.getenv("MONGODB_URI"))

db = client["simdoctor"]
knowledge = db["diagnostic_knowledge"]

print("Testing diagnostic knowledge retrieval...\n")

for document in knowledge.find({}, {"_id": 0}):
    print(document)
    print("-" * 50)

client.close()
