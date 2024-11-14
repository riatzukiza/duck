import chromadb
from shared.mongodb import db
import motor.motor_asyncio

MONGO_CONNECTION_STRING = f"mongodb://{settings.MONGODB_HOST_NAME}/{settings.MONGODB_ADMIN_DATABASE_NAME}"
"""
Types of data sources:
file systems
websites
service apis (discord, twitter/x, reddit, linkedin)
ftp

"""
class VectorIndexedDocumentCollection:
    def __init__(self,name, file_root, chunk_size=100, overlap=0):
        self.name=name
        self._mongo_client = motor.motor_asyncio.AsyncIOMotorClient(CONNECTION_STRING, 27017)
        self._chroma_client = chromadb.PersistentClient(path="./chroma_db")
        self._file_root = file_root

        self._mongodb_collection=self.mongo_client[name]
        self._chroma_collection= self._chroma_client.get_or_create_collection(name=name)

    def insert(self,key,doc,meta_data):
        """
        Insert document into both chroma and mongodb.
        Chroma data will be chunked.
        number of chunks are tracked in mongo.
        mongo contains metadata about the document as a whole.
        """
        self._mongodb_collection.insert_one({
            "key":key,
            "doc":
        })

