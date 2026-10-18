import sqlite3

connection = sqlite3.connect("simdoctor.db")
cursor = connection.cursor()

cursor.execute("PRAGMA table_info(sensor_readings)")

for column in cursor.fetchall():
    print(column)

    connection.close()
    