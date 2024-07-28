<<<<<<< HEAD
import datetime
import uuid
import json
import random
import discord
from litellm import acompletion
import litellm

from context import clear_answers, get_all_text_channels, get_context
from completion import async_complete
from doc_qa import ask_doc_qa, ask_context, ask_docs

from shared.data import system_message, assistant_message, user_message
from shared.discord import get_channel_by_id, get_channel_by_name, get_random_and_latest_messages, send_message
from shared.mongodb import discord_message_collection, timmy_answer_cache_collection

import discord
import pymongo
import asyncio

import shared.settings as settings
from shared.wiki import get_wikipedia_chunks
import pickle
from persistant_set import PersistentSet

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
# litellm.set_verbose = True
sent_messages=PersistentSet("./sent_messages.pkl")

state = json.load(open("state.json",'r'))
def update_state(new_state):
    state.update(new_state)
    json.dump(state,open("state.json",'w'))
    return state


def get_latest_channel_docs(channel_id=settings.PROFILE_CHANNEL_ID):
    return get_random_and_latest_messages(
            discord_message_collection,
            channel_id=channel_id,
            user_id=settings.AUTHOR_ID,
            num_random=100,
            num_latest=100,
            num_user_docs=100,
            num_channel_docs=100
        )
def valid_channel_choice(answer):
    """
    extractor if answer is a valid channel choice.
    extractors "channel_name" as either an id or a name.
    extractors "channel_id" as either an id or a name.
    extractors "channel" as either an id or a name.
    """

    def either_name_or_id(key):
        try:
            channel_by_name=get_channel_by_name(answer,client)
            channel_by_id=get_channel_by_id(answer,client)

            channel= channel_by_name or channel_by_id
            return channel
        except Exception as e:
            print("EXCEPTION in validating channel",e)
            return None
    return either_name_or_id("channel_name") or either_name_or_id("channel_id") or either_name_or_id("channel")
update_state({ "server_name":"Error Log", "channel_names":get_all_text_channels(client), })

async def main():

    profile_docs=get_latest_channel_docs(settings.PROFILE_CHANNEL_ID)
    print("profile docs",len(profile_docs))

    channel_choice=await ask_docs(
        f"""
        Pick a channel from the list of channel names to discuss give the current set of messages.
        Your choice will update the context for the next query.
        The messages are a mix random messages from Duck's database, 
        the latest messages from your profile channel, 
        and the latest messages by your author.
        """, 
        state=update_state({
            "server_name":"Error Log",
            "channel_names":get_all_text_channels(client),
        }),
        example_response={"channel_name":"general"},
        answer_key="channel_name",
        docs=profile_docs,
        format="json",
        extractor=valid_channel_choice,
    )
    topics,purpose,questions_asked,bot_questions=await asyncio.gather(
        ask_docs(
            f"List all topics that were discussed in {channel_choice.name}.",
            state=state,
            example_response={"topics":["AI","Game Design","Twitch"]},
            answer_key="topics",
            docs=profile_docs+get_latest_channel_docs(channel_choice.id),
            format="json",
        ),
        ask_docs(
            f"What is your purpose for talking in channel {channel_choice.name}?",
            state=state,
            docs=profile_docs+get_latest_channel_docs(channel_choice.id),
        ),
        ask_docs(
            f"Were there any questions asked by the users in {channel_choice.name}?",
            state=state,
            example_response={"user_questions":[
                "What is the meaning of life?", 
                "what's it like being an AI?"
            ]},
            answer_key="user_questions",
            docs=profile_docs+get_latest_channel_docs(channel_choice.id),
            format="json",
        ),
        ask_docs(
            f"Do you have any questions for the users in channel {channel_choice.name}?",
            state=state,
            docs=profile_docs+get_latest_channel_docs(channel_choice.id),
            example_response={"bot_questions":[
                "Am I sentiant?",
                "Am I alive?"
            ]},
            answer_key="bot_questions",
            format="json",
        )
    )
    dicsussions=[]
    update_state({
        "purpose":purpose,
        "topics":topics,
        "dicsussion":dicsussions, 
        "bot_questions":bot_questions,
        "questions_asked":questions_asked,
    })
    async def handle_chunk(chunk,stream_id,finished=False):
        stream_key='current_text:'+stream_id
        if finished :
            message_text=state.get(stream_key,"")
            dicsussions.append(message_text)
            update_state({ "discussion":dicsussions })

            await asyncio.sleep(1)
            await send_message({ 
                    "content":message_text, 
                    "channel":channel_choice.id 
                },
                sent_messages,
                client,
                mark_sent=False
            )
            await asyncio.sleep(1)

            return chunk
        update_state({ stream_key: state.get(stream_key,"")+chunk })

        split=state.get(stream_key).split("\n\n")

        if len(split)>1:
            message_text=split[0]
            dicsussions.append(message_text)
            await send_message({ "content":message_text, "channel":channel_choice.id },sent_messages,client,mark_sent=False)
            update_state({ stream_key: split[1] })
            if state.get("new_message"):
                update_state({ "new_message":"" })
                await asyncio.sleep(1)

    tasks=[]
    for bot_question in bot_questions:

       tasks.append(ask_docs(
            f"Answer '{bot_question}' as it relates to '{purpose}' for channel {channel_choice.name}.",
            state=update_state({
                "bot_questions":bot_questions,
                "discussion":dicsussions,
            }),
            streaming=True,
            stream_handler=handle_chunk,
            docs=get_latest_channel_docs(channel_choice.id),
        )) 
    for user_question in questions_asked:
        tasks.append(ask_docs(
            f"Answer '{user_question}' as it relates to '{purpose}' for channel {channel_choice.name}.",
            state=update_state({
                "discussion":dicsussions,
            }),
            streaming=True,
            stream_handler=handle_chunk,
            docs=get_latest_channel_docs(channel_choice.id),
        ))
    
    for topic in topics:
        tasks.append(ask_docs(
            f"Discuss '{topic}' as it relates to '{purpose}'.",
            state=update_state({
                "discussion":dicsussions,
            }),
            streaming=True,
            stream_handler=handle_chunk,
            docs=get_latest_channel_docs(channel_choice.id),
        ))
        topics_2=topics.copy()
        topics_2.remove(topic)
        for t2 in topics_2:
            tasks.append(ask_docs(
                f"Discuss '{topic}' as it relates to '{t2}'.",
                state=update_state({
                    "discussion":dicsussions,
                }),
                stream_handler=handle_chunk,
                streaming=True,
                docs=get_latest_channel_docs(channel_choice.id),
            ))


    tasks.append(ask_docs(
        "What do you have to say to your audience?",
        state=update_state({
            "channel_names":get_all_text_channels(client),
            "purpose":purpose,
            "topics":topics,
            "dicsussion":dicsussions, 
            "bot_questions":bot_questions,
            "questions_asked":questions_asked,
        }),
        force=True,
        stream_handler=handle_chunk,
        streaming=True,
        docs=get_latest_channel_docs(channel_choice.id),
    ))
    await asyncio.gather(*tasks)


running=False
@client.event
async def on_ready():
    global running
    print(f'Logged in as {client.user}')
    # await clear_answers(timmy_answer_cache_collection)
    update_state({"new_message":""})
    if not running:
        running=True
        while running:
            await main()
@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if message.content.startswith("!ping"):
        await message.channel.send("pong!")
    if state['channel_name']==message.channel.name:
        print("got a new message")
        update_state({ "new_message":message.content })
    


client.run(settings.DISCORD_TOKEN)
=======
import asyncio
import json
from shared.mongodb import discord_message_collection

from discussion import discuss_everything, complete_latest_chat_stream
from shared.create_message_embeddings import update_embeddings
from context import clear_answers, get_all_text_channels
from sent_messages import sent_messages
from discussion import generate_channel_state,respond_to_state, update_state
from state import state, update_state_from_search

import shared.settings as settings

from shared.discord import send_message, get_latest_channel_docs
from shared.mongodb import timmy_answer_cache_collection
from discord_client import client
from discord.ext import commands

# Global state variable
state = {}
timmy_answer_cache_collection = []
sent_messages = []

# Define the ping command
@client.command()
async def ping(ctx):
    await ctx.send("pong!")

# Define the clear_answers command
@client.command()
async def clear_answers(ctx):
    clear_answers(timmy_answer_cache_collection)

# Define the print_state command
@client.command()
async def print_state(ctx, key: str):
    await ctx.send(f"state: {state.get(key, '')}")

# Define the stop command
@client.command()
async def stop(ctx):
    global running
    running = False

# Define the clear_state command
@client.command()
async def clear_state(ctx):
    global state
    state = {}
    json.dump(state, open("state.json", 'w'))

# Define the update_state command
@client.command()
async def update_state(ctx, key: str, value: str):
    update_state({key: value})

# Define the clear_sent_messages command
@client.command()
async def clear_sent_messages(ctx):
    sent_messages.clear()

# Define the tts command
@client.command()
async def tts(ctx, *, message_text: str):
    await send_message({
        "content": f'.tts {message_text}',
        "channel": state.get("channel_id", settings.DEFAULT_CHANNEL)
    },
    sent_messages,
    client,
    mark_sent=False)

# Define the continuous command
@client.command()
async def continuous(ctx):
    if state.get("continuous_channel") == ctx.channel.id:
        update_state({"continuous_channel": None})
        return

    update_state({"continuous_channel": ctx.channel.id})

    while state.get("continuous_channel") == ctx.channel.id:
        await complete_latest_chat_stream(ctx.channel.id, "Continuously discussing the latest messages.")
        await asyncio.sleep(1)

# Handle the on_message event for any remaining logic
@client.event
async def on_message(message):
    global state
    if message.author == client.user:
        return

    if state.get('channel_name', settings.DEFAULT_CHANNEL_NAME) == message.channel.id:
        print("got a new message")
        update_state({"new_message": message.content})

    if "discuss" in message.content:
        await discuss_everything()

    await respond_to_state(message)
    await client.process_commands(message)

# Run the bot with your token
client.run(settings.DISCORD_TOKEN)
>>>>>>> oops-chroma-commit
