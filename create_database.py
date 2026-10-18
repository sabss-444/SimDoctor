
import sqlite3

# Create the database file
connection = sqlite3.connect("simdoctor.db")

# Allow us to execute SQL commands
cursor = connection.cursor()

# Create the vehicles table
cursor.execute("""
CREATE TABLE IF NOT EXISTS vehicles (
    vehicle_id INTEGER PRIMARY KEY AUTOINCREMENT,
    make TEXT,
    model TEXT,
    year INTEGER,
    mileage INTEGER
)
""")

# Save the changes
connection.commit()

# Close the connection
connection.close()

print("SimDoctor database created successfully!")
