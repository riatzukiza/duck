"""
Generate messages for discord using DuckGPT.
"""


import datetime
from io import StringIO
import pymongo
import pandas as pd

from shared import settings
from shared.mongodb import discord_message_collection, generated_message_collection
from shared.discord import get_random_and_latest_messages

from shared.data import CSVChunker
from shared.gpt import DuckGPT


duck=DuckGPT()

docs=get_random_and_latest_messages(
    discord_message_collection, 
    user_id=settings.AUTHOR_ID,
    channel_id=settings.PROFILE_CHANNEL_ID,
    num_user_docs=3000,
    num_random=1000, 
    num_latest=2000
)

# filter all mesaages bty 
training_data = CSVChunker(
    name=f"unread_messages_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}",
    cursor=docs,
    chunk_size=1000
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


