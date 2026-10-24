
import os
from pathlib import Path
from dotenv import load_dotenv
from pymongo import MongoClient

# Load the .env file from the main folder
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

uri = os.getenv("MONGODB_URI")

if not uri:
    print("ERROR: MONGODB_URI was not found.")
else:
    print("URI found. Testing connection...")

    try:
        client = MongoClient(
            uri,
            serverSelectionTimeoutMS=10000
        )

        client.admin.command("ping")
        print("SUCCESS: Connected to MongoDB Atlas!")

    except Exception as error:
        print("CONNECTION FAILED")
        print(type(error).__name__)
        print(error)

    finally:
        if "client" in locals():
            client.close()
