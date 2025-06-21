import sqlite3
from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
import os

load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

pc = Pinecone(api_key=PINECONE_API_KEY)

index_name = "hackumass"
if index_name not in pc.list_indexes().names():
    pc.create_index(
        name=index_name,
        dimension=384,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1")
    )
index = pc.Index(index_name)

model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

conn = sqlite3.connect("f1_race_data.db")
cursor = conn.cursor()

def generate_embedding(text):
    return model.encode(text).tolist()

def check_and_store_embedding(text, metadata, entry_id):
    response = index.query(vector=generate_embedding(text), top_k=1, filter=metadata)
    if response.get("matches") and response["matches"][0]["id"] == entry_id:
        print(f"Skipped already embedded entry: {entry_id}")
        return
    embedding = generate_embedding(text)
    index.upsert([(entry_id, embedding, metadata)])
    print(f"Embedded new entry: {entry_id}")

def upload_race_data():
    cursor.execute("SELECT * FROM races")
    races = cursor.fetchall()
    for race in races:
        race_id, season, round_num, race_name, date, circuit_id, circuit_name, location, country = race
        metadata = {
            "type": "race",
            "season": season,
            "round": round_num,
            "race_name": race_name,
            "date": date,
            "circuit_name": circuit_name,
            "location": location,
            "country": country
        }
        text = f"{race_name}, {season} season, {circuit_name}, located in {location}, {country}"
        check_and_store_embedding(text, metadata, entry_id=str(race_id))

    cursor.execute("SELECT * FROM lap_times")
    lap_times = cursor.fetchall()
    for lap in lap_times:
        race_id, driver_id, lap_number, position, time, milliseconds = lap
        metadata = {
            "type": "lap_time",
            "race_id": race_id,
            "driver_id": driver_id,
            "lap_number": lap_number,
            "position": position,
            "time": time,
            "milliseconds": milliseconds
        }
        text = f"Lap {lap_number} of race {race_id} for driver {driver_id} with time {time}."
        check_and_store_embedding(text, metadata, entry_id=f"{race_id}-{lap_number}-{driver_id}")

    cursor.execute("SELECT * FROM drivers")
    drivers = cursor.fetchall()
    for driver in drivers:
        driver_id, code, forename, surname, nationality = driver
        metadata = {
            "type": "driver",
            "driver_id": driver_id,
            "code": code,
            "forename": forename,
            "surname": surname,
            "nationality": nationality
        }
        text = f"Driver {forename} {surname}, nationality {nationality}, code {code}"
        check_and_store_embedding(text, metadata, entry_id=str(driver_id))

    print("Data embedded and stored in Pinecone.")

upload_race_data()
conn.close()
