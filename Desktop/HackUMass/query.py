import os
import google.generativeai as genai
from dotenv import load_dotenv
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer
import numpy as np
import re

load_dotenv()

gemini_api_key = os.getenv("GEMINI_API_KEY")
pinecone_api_key = os.getenv("PINECONE_API_KEY")

if not gemini_api_key:
   print("Error: GEMINI_API_KEY not found in environment variables.")
if not pinecone_api_key:
   print("Error: PINECONE_API_KEY not found in environment variables.")

genai.configure(api_key=gemini_api_key)

pc = Pinecone(api_key=pinecone_api_key)
index = pc.Index("tester")

sentence_model = SentenceTransformer('all-MiniLM-L6-v2')

chat_history = []

current_race = None

def set_current_race(race_name):
    global current_race
    current_race = race_name
    print(f"Context set to: {current_race}")

def detect_race_change(query):
    global current_race
    race_pattern = r'\b(\d{4}\s+[A-Za-z]+\s+GP)\b'
    match = re.search(race_pattern, query, re.IGNORECASE)
    if match:
        new_race = match.group(1)
        if new_race != current_race:
            set_current_race(new_race)

def document_to_vector(document):
   vector = sentence_model.encode(document)
   return vector

def search_documents(query):
    detect_race_change(query)

    if not current_race:
        print("No race context set. Please specify the race.")
        return []

    query_vector = document_to_vector(query)
    query_vector = np.array(query_vector).tolist()

    try:
        results = index.query(vector=query_vector, top_k=5)
        matches = results.get("matches", [])
        if matches:
            return [match.get("metadata", {}) for match in matches]
        else:
            print("No matches found.")
            return []
    except Exception as e:
        print(f"Error during Pinecone search: {e}")
        return []

def generate_response_with_context(query, retrieved_data):
    if retrieved_data:
        context_details = "\n".join([
            f"Race Name: {d.get('race_name', 'N/A')}, Driver: {d.get('driver_name', 'N/A')}, "
            f"Lap Count: {d.get('lap_count', 'N/A')}, Lap Time: {d.get('lap_time', 'N/A')}"
            for d in retrieved_data
        ])
    else:
        context_details = "No specific data available from Pinecone."

    prompt = f"""
    You are assisting a user with questions about the {current_race} in Formula 1.

    User query: '{query}'

    Relevant information from Pinecone:
    {context_details}

    Based on this information, please provide a detailed and accurate response about the {current_race}.
    If additional general knowledge is needed to answer the query, incorporate it. Specify clearly if the response is based on data from Pinecone or your general knowledge.
    """

    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error during response generation: {e}")
        return "Error: Unable to generate response from Gemini."

def add_to_chat_history(query, response):
    global chat_history
    if len(chat_history) >= 5:
        chat_history.pop(0)
    chat_history.append({"query": query, "response": response})

def main():
    global chat_history

    initial_race = input("Which race are you watching (e.g., '2020 Turkey GP')? ")
    set_current_race(initial_race)

    while True:
        user_query = input("Please enter your query (or type 'exit' to quit): ")

        if user_query.lower() == "exit":
            print("Exiting the program.")
            break

        retrieved_data = search_documents(user_query)

        if retrieved_data:
            response = generate_response_with_context(user_query, retrieved_data)
            print(response)
            add_to_chat_history(user_query, response)
        else:
            print("No relevant documents found in Pinecone.")

if __name__ == "__main__":
    main()
