
class ContextManager:
    def __init__(self,mongo_collections=[]):
        self.mongo_collections = mongo_collections
        self.chroma_client = chromadb.PersistentClient(path="./chroma_db")
        self.chroma_collections = {
            name:self.chroma_client.get_or_create_collection(name=name) for name in mongo_collections
        }
    def index_document_batch(self,documents):

    def index_mongodb_collection(self,name):
        collection=mongo_db[name]
        documents=collection.find().limit(1000)

    def update(self,new_context):
        self.context.update(new_context)
        json.dump(self.context,open("context.json",'w'))
        return self.context

    def get(self,key,default=None):
        return self.context.get(key,default)
    
    async def query(self,question,key,example,get_docs=get_latest_channel_docs):
        return generate_context_property_update(question,key,example,get_docs)
class StateManager:
    """ 
    Class to manage the state of the Duckman bot.
    """
    def __init__(self):
        self.state = json.load(open("state.json",'r'))

    def update(self,new_state):
        self.state.update(new_state)
        json.dump(self.state,open("state.json",'w'))
        return self.state

    def get(self,key,default=None):
        return self.state.get(key,default)
    
    async def query(self,question,key,example,get_docs=get_latest_channel_docs):
        return generate_state_property_update(question,key,example,get_docs)
class EmbededingManager:
    def __init__(self):
        self.embeddings = json.load(open("embeddings.json",'r'))

    def update(self,new_embeddings):
        self.embeddings.update(new_embeddings)
        json.dump(self.embeddings,open("embeddings.json",'w'))
        return self.embeddings

    def get(self,key,default=None):
        return self.embeddings.get(key,default)
    
    async def query(self,question,key,example,get_docs=get_latest_channel_docs):
        return generate_embedding_property_update(question,key,example,get_docs)