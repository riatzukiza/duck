"""This service creates messages from the model and saves them in mongodb"""
import datetime

from shared import settings
from shared.data import CSVChunker
from shared.discord import get_latest_messages, get_read_messages, get_unread_messages,mark_messages_as_read, get_random_and_latest_messages
from shared.gpt import DuckGPT
from shared.mongodb import discord_message_collection

import pymongo

duck=DuckGPT()

docs=get_random_and_latest_messages(
    discord_message_collection, 
    user_id=settings.AUTHOR_ID, 
    channel_id=settings.PROFILE_CHANNEL_ID,
    num_random=1000, 
    num_latest=2000,
    num_user_docs=5000
) 

data = CSVChunker(
    name=f"unread_messages_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}",
    cursor=docs,
    chunk_size=100
)
training_data=data.csvs
print(training_data)
duck.train(training_data)