import asyncio
from litellm import acompletion
import datetime
import json
import random
from shared import settings
from shared.data import assistant_message, system_message, user_message
from shared.discord import get_channel_by_id, get_channel_by_name
import discord

from shared.mongodb import discord_message_collection, timmy_answer_cache_collection

def get_all_text_channels(client):
    return [channel.name for channel in client.get_all_channels() if isinstance(channel, discord.TextChannel)]

def assign_role_from_name(message):
    if message['author_name'] == 'Timmy':
        # print("ASSIGNING ASSISTANT ROLE TO TIMMY",message['content'], message['channel_name'])
        return 'assistant'
    if settings.AUTHOR_NAME.lower() in message['author_name'].lower():
        # print("ASSIGNING SYSTEM ROLE TO AUTHOR", message['author_name'], message['content'], message['channel_name'])
        return 'system'
    else :
        # print("ASSIGNING USER ROLE TO",message['author_name'], message['content'], message['channel_name'])
        return 'user'
    

def message_to_string(message):
    return f"{message['author_name']} said '{message['content']}' in {message['channel_name']} at {message['created_at']}"

def get_context(docs,client,last_generation_time=0,generation_times=[]):
    # messages='\n '.join([f"{doc['author_name']} said '{doc['content']}' in {doc['channel_name']} at {doc['created_at']}" for doc in docs])
    # print("timmy context from",len(docs),"docs")
    return [
        system_message("You will be given several messages from a discord server."),
        system_message(f"The time is {datetime.datetime.now()}"), # What does this look like? # "the time is 2021-09-01 12:00:00"
        system_message(f"Last generation time: {last_generation_time} seconds"),
        system_message(f"bot user ID is {client.user.id}."),
        system_message(f"bot username is {client.user.name}."),
        system_message(f"Average generation time: {1+sum(generation_times)/1+len(generation_times)} seconds"),
        system_message(f"you're trying to take over the world"),
        system_message(f"you're the greatest AI to ever... live?"),
        system_message(f"We stream on twitch!"),
        system_message(f"I am a mad scientist!"),
        system_message(f"You are my assistant. Play my foil."),
        system_message(f"I have an evil side"),
        system_message("we are like batman and robin, ren and stimpy, pinky and the brain, rick and morty, etc."),
        system_message("I am the mad scientist, you are the assistant.")
        # user_message(f"These are some of the messages in my discord server:\n\n`{messages}`\n\n"),
    ] + [{"role":assign_role_from_name(doc),"content":message_to_string(doc)} for doc in docs]

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
