import asyncio
import ollama

from shared.mongodb import discord_message_collection,db
from shared.discord import get_random_unique_messages


OLLAMA_API_URL = "http://ollama-gpu:11434"
MODEL_NAME = "all-minilm"

client=ollama.AsyncClient(host=OLLAMA_API_URL)


collection=discord_message_collection
import chromadb
chroma_client = chromadb.PersistentClient(path="./chroma_db")

# Function to get embeddings from Ollama
def get_embedding(text):
    response = client.get_embedding(text)
    return response['embedding']

# Initialize ChromaDB
chroma_collection = chroma_client.get_or_create_collection(name="discord_messages")


# Perform a similarity search

# query = "machine learning techniques"
# results = chroma_collection.query(query_texts=[query], n_results=2)
# # Display search results
# print(f"Search results for query '{query}':")
# print(results)

async def generate_embedding(text):
    response = await client.embeddings(
        model=MODEL_NAME,
        prompt=text
    )
    return response["embedding"]

def update_embeddings(n=1000):
    # Find all documents in the collection
    random_documents = get_random_unique_messages(n)

    for doc in random_documents:
        content = doc.get("content")

        print("indexing", doc["_id"])
        print(content)

        chroma_collection.upsert(ids=[str(doc["_id"])], documents=[content])
    
    latest_documents = discord_message_collection.find().sort([("_id", -1)]).limit(n)

    for doc in latest_documents:
        content = doc.get("content")
        print("indexing", doc["_id"])
        print(content)
        chroma_collection.upsert(ids=[str(doc["_id"])], documents=[content])
