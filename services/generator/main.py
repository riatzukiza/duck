"""
Generate messages for discord using DuckGPT.
"""


import datetime
from io import StringIO
import pymongo
import pandas as pd

from shared.mongodb import discord_message_collection, generated_message_collection

from shared.data import CSVChunker
from shared.gpt import DuckGPT


duck=DuckGPT()

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
        {"$match": {"author_name":{
            "$nin":[None,"","Roarar","Duck"]
        } }}
    ]

    # Aggregation pipeline for latest messages by a specific user
    user_docs_pipeline = [
        {"$match": {"user_id": user_id}},

        {"$sort": {"created_at": -1}},
        {"$limit": num_user_docs}
    ]

    latest_docs_pipeline = [
        {"$match": {"content":{
            "$not":{
                "$regex":r"(youtube.com|pplx.ai)","$options":"i"
            },
            "$nin":[None, "",".featured"]
        }}},
        {"$match": {"author_name":{
            "$nin":[None,"","Roarar","Duck"]
        } }},
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
    num_user_docs=300,
    num_random=10, 
    num_latest=20
)
combined_docs = random_docs+latest_docs+user_docs
# print(combined_docs)
combined_docs.sort(key=lambda x: x['created_at'])

# filter all mesaages bty 
training_data = CSVChunker(
    name=f"unread_messages_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}",
    cursor=combined_docs,
    chunk_size=100
)

generated_text=duck.generate(training_data.last.csv)

df=pd.read_csv(StringIO(generated_text))

for index, row in df.iterrows():
    generated_message_collection.insert_one({
        "sent": False,
        "content": row['content'],
        "channel":row["channel"]
    })

# Save the generated messages to the database


