# Query and display contents of the "races" table
print("Races Table:")
for row in cursor.execute("SELECT * FROM races LIMIT 10"):  # Limit to 10 rows for readability
    print(row)

# Query and display contents of the "drivers" table
print("\nDrivers Table:")
for row in cursor.execute("SELECT * FROM drivers LIMIT 10"):
    print(row)

# Query and display contents of the "lap_times" table
print("\nLap Times Table:")
for row in cursor.execute("SELECT * FROM lap_times LIMIT 10"):
    print(row)
