
import sqlite3

connection = sqlite3.connect("simdoctor.db")
connection.execute("PRAGMA foreign_keys = ON")
cursor = connection.cursor()

# 1. Insert a test vehicle
cursor.execute("""
INSERT INTO vehicles (make, model, year, mileage)
VALUES (?, ?, ?, ?)
""", ("Ford", "Fiesta", 2018, 65000))

vehicle_id = cursor.lastrowid

# 2. Save a chatbot conversation
cursor.execute("""
INSERT INTO conversations
(vehicle_id, user_message, ai_response)
VALUES (?, ?, ?)
""", (
    vehicle_id,
    "My car makes a squeaking noise when I brake.",
    "Possible causes include worn brake pads or surface corrosion. Further inspection is needed."
))

conversation_id = cursor.lastrowid

# 3. Save a diagnostic report
cursor.execute("""
INSERT INTO diagnostic_reports
(conversation_id, suspected_cause, evidence, urgency, recommendation)
VALUES (?, ?, ?, ?, ?)
""", (
    conversation_id,
    "Possible brake pad wear",
    "The user reports squeaking during braking. No physical inspection has been performed.",
    "Inspection recommended",
    "Arrange a brake inspection. Seek urgent help if braking performance is reduced or grinding occurs."
))

# Save all changes
connection.commit()

# 4. Retrieve the report
cursor.execute("""
SELECT
    vehicles.make,
    vehicles.model,
    conversations.user_message,
    diagnostic_reports.suspected_cause,
    diagnostic_reports.recommendation
FROM diagnostic_reports
JOIN conversations
    ON diagnostic_reports.conversation_id = conversations.conversation_id
JOIN vehicles
    ON conversations.vehicle_id = vehicles.vehicle_id
""")

reports = cursor.fetchall()

print("SIMDOCTOR TEST REPORTS")
print("----------------------")

for report in reports:
    print("Vehicle:", report[0], report[1])
    print("User's problem:", report[2])
    print("Possible cause:", report[3])
    print("Recommendation:", report[4])
    print()

connection.close()
