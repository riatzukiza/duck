import datetime
import json
import random
import discord
from litellm import acompletion

from shared.data import CSVChunker, assistant_message, system_message
from shared.discord import get_random_and_latest_messages, send_message
from shared.mongodb import discord_message_collection

import discord
import pymongo
import asyncio

import shared.settings as settings

intents = discord.Intents.default()
client = discord.Client(intents=intents)

sent_messages=set()

def message_template(message):
    return f"{message['author_name']} said at {message['created_at']}: {message['content']} in channel {message['channel_name']}."

def format_messages(docs):
    return [message_template(doc) for doc in docs]

def message_group_template(name,description,docs):
    return f"""
    # {name}
    {description}
    ### Messages:
    {len(docs)} messages:
    {format_messages(docs)}
    """
    
    
# def user_message(name,description,docs):
#     return {
#         "content":message_group_template(name,description,docs),
#         "role":"user"
#     }

def user_message(content):
    return {
        "content":content,
        "role":"user"
    }
async def main(
    last_generation_time=0,
    start_time=datetime.datetime.now(),
    end_time=datetime.datetime.now(),
    generation_times=[]
):
    docs=get_random_and_latest_messages(
        discord_message_collection, 
        user_id=settings.AUTHOR_ID,
        channel_id=settings.PROFILE_CHANNEL_ID,
        num_random=100, # How many random messages?
        num_latest=300,# How many latest messages?
        num_user_docs=500 # How many docs from the author.
    )


    # filter all mesaages bty 
    training_data = CSVChunker(
        name=f"unread_messages_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}",
        cursor=docs,
        chunk_size=500
    )
    # only the id and channel name.

    # a list of Every channel id and namefrom the discord client
    channels=[  (channel.id,channel.name) for channel in client.get_all_channels() ] 
    # print(channels)
    
    context=[
        system_message('Respond with a json array list of messages . {"messages":[{"content": "Hi I\'m timmy!", "channel_id": 1234567890}]}'), 
        system_message(f"A list of channel id/name pairs: {channels}"),
        system_message("The messages from discord are in CSV chunks."),
    ] + list( map(lambda x: user_message(x), list(training_data.csvs)))
    # for message in context:
    #     print(message)



    response=await acompletion(
        model="ollama_chat/llama3",
        messages=context,
        max_tokens=2000,
        api_base="http://ollama:11434",
        format="json"
    )

    to_send=response.choices[0].message.tool_calls
    print(to_send)
    for message in to_send:
        for message in json.loads(message.function.arguments)['messages']:
            print(message)
            await send_message({
                "content":message['content'],
                "channel":message.get('target_channel',str(settings.DEFAULT_CHANNEL))
            },sent_messages,client,mark_sent=False)
    end_time=datetime.datetime.now()
    last_generation_time=(end_time-start_time).total_seconds()
    generation_times.append(last_generation_time)


@client.event
async def on_ready():
    print(f'Logged in as {client.user}')
    while True:
        await main()





client.run(settings.DISCORD_TOKEN)
