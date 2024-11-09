import pinecone
import openai
import os
from sentence_transformers import Sentence

#OpenAI API Key
openai.api_key = os.getenv('OPENAI_API_KEY')

#Get the Pinecone API Key and environment
pinecone.init(api_key='PINECONE_API_KEY', environemnt= 'PINECONE_ENVIRONMENT')

#Set index; It must exist in order to access Pinecone 
index = pinecone.Index("hackumass") #https://docs.pinecone.io/guides/data/target-an-index

def store_scraped_data(race_data):
    for race in race_data:
        for lap in race["lap_times"]:
            text_data = f"{race['race_name']} {race['year']} {lap['driver_name']} {lap['lap_time']}"
            
            embedding = openai.Embedding.create(input=text_data, model="text-embedding-3-large")['data'][0]['embedding']
            
            # Metadata for retrieval
            metadata = {
                "race_name": race["race_name"],
                "year": race["year"],
                "driver_name": lap["driver_name"],
                "lap_time": lap["lap_time"]
            }
            
            # Upsert data to Pinecone
            index.upsert([
                {
                    "id": f"{race['year']}_{race['race_name']}_{lap['driver_name']}",
                    "values": embedding,
                    "metadata": metadata
                }
            ])
