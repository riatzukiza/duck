from fastapi import FastAPI, HTTPException
import motor.motor_asyncio
from shared import settings
import chromadb
app = FastAPI()

CONNECTION_STRING = f"mongodb://{settings.MONGODB_HOST_NAME}/{settings.MONGODB_ADMIN_DATABASE_NAME}"
client = motor.motor_asyncio.AsyncIOMotorClient(CONNECTION_STRING, 27017)


@app.get("/collections/{collection}/")
async def read_collection(collection:str, limit:int=10, skip:int=0,channel_name:str="duck-bots",user_name:str=""):
    collection = client[settings.MONGODB_ADMIN_DATABASE_NAME][collection]
    docs = await collection.aggregate([
        {"$sort": {"_id": -1}},
        {"$match": {"channel_name": {"$regex": channel_name, "$options": "i"}, 
                    "author_name": {"$regex": user_name, "$options": "i" }}},
        {"$skip": skip},
        {"$limit": limit}
    ]).to_list(limit)
    print("docs",docs   )

    return list(map(lambda doc: {**doc, "_id": str(doc["_id"])}, docs))

@app.get("/search_results/{collection}/")
async def search_results(collection:str, search:str, limit:int=10):
    chroma_client = chromadb.PersistentClient(path="./chroma_db")
    chroma_collection = chroma_client.get_or_create_collection(name=collection)
    
    docs=chroma_collection.query(query_texts=[search], n_results=limit)
    return docs

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)