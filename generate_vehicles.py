
import random

# UK registration format: 2 letters, 2 digits, 3 letters
LETTERS = "ABCDEFGHJKLMNOPRSTUVWXYZ"
DIGITS = "0123456789"

MAKES_AND_MODELS = {
    "Ford": ["Fiesta", "Focus", "Puma"],
    "Toyota": ["Yaris", "Corolla", "Auris"],
    "Volkswagen": ["Golf", "Polo", "Passat"],
    "BMW": ["1 Series", "3 Series", "5 Series"],
    "Vauxhall": ["Corsa", "Astra", "Mokka"],
    "Honda": ["Civic", "Jazz", "HR-V"],
}

def generate_registration():
    """Generate a UK-style fictional registration."""
    area = "".join(random.choices(LETTERS, k=2))
    age = f"{random.randint(0, 99):02d}"
    suffix = "".join(random.choices(LETTERS, k=3))
    return f"{area}{age} {suffix}"

def generate_vehicles(number=10):
    """Generate fictional vehicles with unique registration numbers."""
    vehicles = []
    registrations = set()

    for _ in range(number):
        while True:
            registration = generate_registration()
            if registration not in registrations:
                registrations.add(registration)
                break

        make = random.choice(list(MAKES_AND_MODELS.keys()))
        model = random.choice(MAKES_AND_MODELS[make])

        vehicles.append({
            "registration_number": registration,
            "make": make,
            "model": model,
            "year": random.randint(2015, 2025),
            "mileage": random.randrange(5000, 150001, 1000),
        })

    return vehicles

if __name__ == "__main__":
    cars = generate_vehicles(10)

    for car in cars:
        print(car)
