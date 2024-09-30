import asyncio
import ollama
from shared.embeddings import generate_embedding
from shared.mongodb import discord_message_collection
import chromadb

chroma_client=chromadb.PersistentClient(path="./chroma_db")
discord_chroma=chroma_client.get_or_create_collection(name="discord_messages")

async def main():
    while True:
        docs=discord_message_collection.find({
            "embedding":{ "$exists": False }
        }).limit(100)

        for doc in docs:
            text=doc["content"]
            if not text:
                discord_message_collection.delete_one({"_id":doc["_id"]})
                continue
            embedding = await generate_embedding(text)
            discord_message_collection.update_one(
                {"_id":doc["_id"]},
                {"$set":{"embedding":embedding}}
            )
            discord_chroma.upsert(embeddings=[embedding],ids=[str(doc["_id"])])
asyncio.run(main())