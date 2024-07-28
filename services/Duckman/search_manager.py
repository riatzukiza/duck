import asyncio
from io import BytesIO
import json
import random
import os

from shared import settings

def get_file_extension(file_path):
    _, file_extension = os.path.splitext(file_path)
    return file_extension


from sent_messages import sent_messages
from shared.discord import get_latest_channel_docs, send_message, split_markdown
from shared.doc_qa import ask_docs
from shared.persistant_set import PersistentSet
from shared.mongodb import discord_message_collection,db
from shared.mongodb import db as mongo_db
from state import update_state_from_search,state

async def main():
    while True:
        messages=get_latest_channel_docs(state.get("channel_id",settings.DEFAULT_CHANNEL))
        choice=random.choice(messages)
        await update_state_from_search(
            choice['content'],
            "random_message"
        )
        await asyncio.sleep(60)

asyncio.run(main())