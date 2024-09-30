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

