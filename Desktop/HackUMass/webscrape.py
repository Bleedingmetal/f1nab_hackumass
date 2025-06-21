import requests
import sqlite3
import time

conn = sqlite3.connect('f1_race_data.db')
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS races (
    race_id TEXT PRIMARY KEY,
    season INTEGER,
    round INTEGER,
    race_name TEXT,
    date TEXT,
    circuit_id TEXT,
    circuit_name TEXT,
    location TEXT,
    country TEXT
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS drivers (
    driver_id TEXT PRIMARY KEY,
    code TEXT,
    forename TEXT,
    surname TEXT,
    nationality TEXT
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS lap_times (
    race_id TEXT,
    driver_id TEXT,
    lap INTEGER,
    position INTEGER,
    time TEXT,
    milliseconds INTEGER,
    FOREIGN KEY (race_id) REFERENCES races (race_id),
    FOREIGN KEY (driver_id) REFERENCES drivers (driver_id)
)
''')

conn.commit()

def fetch_data(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching data: {response.status_code}")
        return None

driver_cache = {}

for season in range(2000, 2025):
    print(f"Fetching data for season {season}...")
    races_url = f'http://ergast.com/api/f1/{season}.json'
    races_data = fetch_data(races_url)
    if not races_data:
        print(f"No data found for season {season}")
        continue

    races = races_data['MRData']['RaceTable']['Races']
    for race in races:
        race_id = race['url'].split('/')[-1]

        cursor.execute("SELECT 1 FROM races WHERE race_id = ?", (race_id,))
        if cursor.fetchone():
            print(f" - Skipping already processed race: {race_id}")
            continue

        race_name = race['raceName']
        round_number = int(race['round'])
        date = race['date']
        circuit = race['Circuit']
        circuit_id = circuit['circuitId']
        circuit_name = circuit['circuitName']
        location = circuit['Location']
        locality = location['locality']
        country = location['country']

        cursor.execute('''
        INSERT OR IGNORE INTO races (race_id, season, round, race_name, date, circuit_id, circuit_name, location, country)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (race_id, season, round_number, race_name, date, circuit_id, circuit_name, locality, country))

        print(f" - Processed race: {race_name} (Round {round_number})")

        laps_url = f'http://ergast.com/api/f1/{season}/{round_number}/laps.json?limit=2000'
        laps_data = fetch_data(laps_url)
        if not laps_data or 'Laps' not in laps_data['MRData']['RaceTable']['Races'][0]:
            print(f"   No lap data found for race: {race_name}")
            continue

        laps = laps_data['MRData']['RaceTable']['Races'][0]['Laps']
        for lap in laps:
            lap_number = int(lap['number'])
            timings = lap['Timings']
            for timing in timings:
                driver_id = timing['driverId']
                position = int(timing['position'])
                time_str = timing['time']

                try:
                    time_parts = time_str.split(':')
                    if len(time_parts) == 2:
                        minutes, seconds = map(float, time_parts)
                        milliseconds = int(minutes * 60000 + seconds * 1000)
                    elif len(time_parts) == 3:
                        hours, minutes, seconds = map(float, time_parts)
                        milliseconds = int(hours * 3600000 + minutes * 60000 + seconds * 1000)
                    else:
                        print(f"Unexpected time format: {time_str}")
                        milliseconds = None
                except ValueError:
                    print(f"Error parsing time: {time_str}")
                    milliseconds = None

                if milliseconds is not None:
                    if driver_id not in driver_cache:
                        driver_url = f'http://ergast.com/api/f1/drivers/{driver_id}.json'
                        driver_data = fetch_data(driver_url)
                        if driver_data:
                            driver_info = driver_data['MRData']['DriverTable']['Drivers'][0]
                            code = driver_info.get('code', '')
                            forename = driver_info['givenName']
                            surname = driver_info['familyName']
                            nationality = driver_info['nationality']

                            driver_cache[driver_id] = (code, forename, surname, nationality)
                            cursor.execute('''
                            INSERT OR IGNORE INTO drivers (driver_id, code, forename, surname, nationality)
                            VALUES (?, ?, ?, ?, ?)
                            ''', (driver_id, code, forename, surname, nationality))
                    else:
                        code, forename, surname, nationality = driver_cache[driver_id]

                    cursor.execute('''
                    INSERT INTO lap_times (race_id, driver_id, lap, position, time, milliseconds)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ''', (race_id, driver_id, lap_number, position, time_str, milliseconds))
                else:
                    print(f"Skipping lap time due to parsing error: {time_str}")

        time.sleep(0.25)

    conn.commit()
    print(f"Data committed for season {season}")

conn.close()
print("Data collection complete.")
