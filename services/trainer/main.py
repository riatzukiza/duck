"""This service creates messages from the model and saves them in mongodb"""
import datetime

from shared.data import CSVChunker
from shared.discord import get_latest_messages, get_read_messages, get_unread_messages,mark_messages_as_read
from shared.gpt import DuckGPT
from shared.mongodb import discord_message_collection

import pymongo

duck=DuckGPT()
print("chunking")

def get_random_and_latest_messages(collection, user_id, num_user_docs=100,num_random=5, num_latest=5):
    # Aggregation pipeline for random messages
    random_pipeline = [
        {"$sample": { "size": num_random } },
        {"$match": {"content":{
            "$not":{
                "$regex":r"(youtube.com|pplx.ai)","$options":"i"
            },
            "$nin":[None, "",".featured"]
        }}},
        {"$match": {"author":{
            "$not":{
                "$regex":r"(roarar|duck)","$options":"i"
            },
        }}}
    ]

    # Aggregation pipeline for latest messages by a specific user
    user_docs_pipeline = [
        {"$match": {"user_id": user_id}},
        {"$sort": {"created_at": -1}},
        {"$limit": num_user_docs}
    ]

    latest_docs_pipeline = [
        {"$sort": {"created_at": -1}},
        {"$limit": num_latest}
    ]

    random_docs = list(collection.aggregate(random_pipeline))
    user_docs = list(collection.aggregate(user_docs_pipeline))
    latest_docs = list(collection.aggregate(latest_docs_pipeline))


    return random_docs, user_docs, latest_docs

random_docs,user_docs,latest_docs=get_random_and_latest_messages(
    discord_message_collection, 
    205909976768708608, 
    num_random=300, 
    num_latest=2000
)

data = CSVChunker(
    name=f"unread_messages_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}",
    cursor=random_docs+latest_docs+user_docs,
    chunk_size=100
)
training_data=data.csvs
print(training_data)
duck.train(training_data)