
import os
from pathlib import Path
from dotenv import load_dotenv
from pymongo import MongoClient

env_path = Path(__file__).parent / "main" / ".env"
load_dotenv(env_path)

uri = os.getenv("MONGODB_URI")

if not uri:
    print("ERROR: MongoDB URI was not found.")
else:
    print("URI found. Testing Atlas connection...")

    try:
        client = MongoClient(
            uri,
            serverSelectionTimeoutMS=10000,
            connectTimeoutMS=10000,
        )

        print("Server response:", client.admin.command("ping"))
        print("SUCCESS: Connected to Atlas!")

    except Exception as error:
        print("Connection failed.")
        print("Error type:", type(error).__name__)
        print("Details:", error)

    finally:
        if "client" in locals():
            client.close()
