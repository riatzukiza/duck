import chromadb
from shared.mongodb import discord_message_collection
from shared.embeddings import generate_embedding
from shared.discord import get_channel_by_id, get_channel_by_name, get_latest_channel_docs
from shared import settings

chroma_client = chromadb.PersistentClient(path="./chroma_db")

file_chroma = chroma_client.get_or_create_collection(name="duckman_files")
message_chroma = chroma_client.get_or_create_collection(name="discord_messages")
search_chroma = chroma_client.get_or_create_collection(name="search-results")

def get_messages_by_ids(ids):
    return list(discord_message_collection.find({'_id': {'$in': ids}}).sort([("created_at", -1)]))

def get_related_messages(question_embedding):
    return get_messages_by_ids(
        message_chroma.query(
            query_embeddings=[question_embedding], n_results=200)['ids'][0])

def get_related_files(question_embedding):
    return file_chroma.query(
            query_embeddings=[question_embedding], n_results=20)['documents'][0]

def get_search_results(question_embedding):
    search_chroma.query(
        query_embeddings=[question_embedding], n_results=20)['documents'][0]

async def get_documents(question, channel_id):

    question_embedding = await generate_embedding(question)
    relevent_messages  = get_related_messages(question_embedding)
    relevent_files     = get_related_messages(question_embedding)
    search_results     = get_search_results(question_embedding)
    profile_messages   = get_latest_channel_docs(settings.PROFILE_CHANNEL_ID)

    unique_docs=set()

    def is_unique_document(doc):
        if doc['_id'] in unique_docs:
            return False
        else:
            unique_docs.add(doc['_id'])
            return True

    messages=list(filter(is_unique_document,
                         get_latest_channel_docs(channel_id)+
                         profile_messages+
                         relevent_messages)
                  ).sort(key=lambda x: x['created_at'])

    return messages, search_results, relevent_files
