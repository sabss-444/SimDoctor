
import os
import random
from pathlib import Path

from dotenv import load_dotenv
from pymongo import MongoClient


# Load MongoDB credentials from .env
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

# Vehicle data
LETTERS = "ABCDEFGHJKLMNOPRSTUVWXYZ"

MAKES_AND_MODELS = {
    "Ford": ["Fiesta", "Focus", "Puma"],
    "Toyota": ["Yaris", "Corolla", "Auris"],
    "Volkswagen": ["Golf", "Polo", "Passat"],
    "BMW": ["1 Series", "3 Series", "5 Series"],
    "Vauxhall": ["Corsa", "Astra", "Mokka"],
    "Honda": ["Civic", "Jazz", "HR-V"],
}


def generate_registration():
    """Generate a fictional UK-style registration."""
    area = "".join(random.choices(LETTERS, k=2))
    age = f"{random.randint(0, 99):02d}"
    suffix = "".join(random.choices(LETTERS, k=3))

    return f"{area}{age} {suffix}"


def generate_vehicles(number=10):
    """Generate fictional vehicle records."""
    vehicles = []
    registrations = set()

    for _ in range(number):
        # Avoid duplicate registrations within this batch
        while True:
            registration = generate_registration()
            if registration not in registrations:
                registrations.add(registration)
                break

        make = random.choice(list(MAKES_AND_MODELS.keys()))
        model = random.choice(MAKES_AND_MODELS[make])

        vehicle = {
            "registration_number": registration,
            "make": make,
            "model": model,
            "year": random.randint(2015, 2025),
            "mileage": random.randrange(5000, 150001, 1000),
        }

        vehicles.append(vehicle)

    return vehicles


def main():
    uri = os.getenv("MONGODB_URI")

    if not uri:
        print("ERROR: MONGODB_URI was not found in main/.env")
        return

    client = None

    try:
        client = MongoClient(
            uri,
            serverSelectionTimeoutMS=10000,
        )

        # Check the connection
        client.admin.command("ping")
        print("Connected successfully to MongoDB Atlas!")

        # Select the database and collection
        db = client["simdoctor"]
        vehicles_collection = db["vehicles"]

        # Generate and save vehicles
        cars = generate_vehicles(10)
        inserted = 0

        for car in cars:
            result = vehicles_collection.update_one(
                {"registration_number": car["registration_number"]},
                {"$setOnInsert": car},
                upsert=True,
            )

            if result.upserted_id is not None:
                inserted += 1

        print(f"\nGenerated {len(cars)} vehicle records.")
        print(f"Added {inserted} new vehicles to Atlas.")

        # Display vehicles currently saved in the collection
        print("\nVehicles stored in MongoDB:")

        for car in vehicles_collection.find(
            {},
            {"_id": 0},
        ).sort("registration_number", 1):
            print(
                f"{car['registration_number']} | "
                f"{car['make']} {car['model']} | "
                f"Year: {car['year']} | "
                f"Mileage: {car['mileage']:,}"
            )

    except Exception as error:
        print("ERROR: Could not complete the vehicle database operation.")
        print(type(error).__name__)
        print(error)

    finally:
        if client is not None:
            client.close()


if __name__ == "__main__":
    main()
