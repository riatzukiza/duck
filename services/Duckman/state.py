
"""Tools for managing the state that persists between contexts.
"""
import json
import random
import os

import chromadb

def get_file_extension(file_path):
    _, file_extension = os.path.splitext(file_path)
    return file_extension


from shared.discord import get_documents_by_ids, get_latest_channel_docs
from shared.doc_qa import ask_docs


state = json.load(open("state.json",'r'))


chroma_client = chromadb.PersistentClient(path="./chroma_db")
search_chroma = chroma_client.get_or_create_collection(name="search_results")
discord_chroma = chroma_client.get_or_create_collection(name="discord_messages")

def update_state(new_state):
    state.update(new_state)
    json.dump(state,open("state.json",'w'))
    return state

async def generate_state_property_update( question,key,example,get_docs=get_latest_channel_docs):

    discord_similar_docs = get_documents_by_ids(discord_chroma.query(query_texts=[question], n_results=10)['ids'][0])
    search_results= search_chroma.query(query_texts=[question], n_results=10)['documents'][0]
    value=await ask_docs(
        f"Update {key} with response to '{question}'.",
        example_response={key:example},
        answer_key=key,
        docs=get_docs()+discord_similar_docs,
        format="json",
        search_results=search_results,
        expires_in=random.randint(1,60)*60,
    )
    update_state({key:value})
    return value
