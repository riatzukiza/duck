import asyncio
from litellm import acompletion
import datetime
import json
import random
from shared import settings
from shared.data import assistant_message, system_message, user_message
from shared.discord import get_channel_by_id, get_channel_by_name
import discord
from discord_client import client

from shared.mongodb import discord_message_collection, timmy_answer_cache_collection

def get_all_text_channels(client):
    return [channel.name for channel in client.get_all_channels() if isinstance(channel, discord.TextChannel)]

def assign_role_from_name(message):
    if message['author_name'] == 'Duck':
        return 'assistant'
    # if settings.AUTHOR_NAME.lower() in message['author_name'].lower()  in message['author_name'].lower() or "jim" in message['author_name'].lower():
    #     return 'system'
    else :
        # print("ASSIGNING USER ROLE TO",message['author_name'], message['content'], message['channel_name'])
        return 'user'
    

def message_to_string(message):
    author = message['author_name'].replace("[Scriptly] ", "")  # Replace "remove" with the substring you want to remove
    return f"User {author} said '{message['content']}' in channel {message['channel_name']} at {message['created_at']}"

def get_context(docs,search_results=[],relavent_files=[]):
    # print("DOCS",docs)
    print("SEARCH RESULTS",search_results)
    print("RELAVANT FILES",relavent_files)

    file_messages=''.join([doc for doc in relavent_files if doc is not None])
    search_messages=''.join([doc + "\n\n" for doc in search_results])
    discord_messages=''.join([message_to_string(doc) for doc in docs if valid_message_content(doc) is not None])

    return [
        system_message(f"""
    The time is {datetime.datetime.now()}
The current date is {datetime.datetime.now().date()}
The user error0815 is your developer.
You are a discord bot who responds differently to queries based on the channel the message was sent in.
You'll adjust your tone according to the title of each channel. For example, if the channel is named 'general', you might respond in a friendly and casual manner, while in a channel named 'support', you would be more formal and helpful.
Here are the messages from the discord server:
{discord_messages}
Here are the search results:
{search_messages}
"Here are the files:
{file_messages}
        """)
    ]
def valid_message_content(message):
    message=message.get('content',message.get('text',message.get('message')))
    return message


def valid_list_of_strings(message,key):
    li = message.get(key,None)
    if not li: return None

    unique_strings=set()

    for string in li: unique_strings.add(string)
    return list(unique_strings)
    

def valid_conversation_topics(message):
    return valid_list_of_strings(message,"topics")

async def clear_answers(collection):
    """_summary_
    empties the collection of answers.
    Args:
        collection (_type_): _description_
    """
    for answer in list(collection.find({})):
        collection.delete_one({"_id":answer["_id"]})
