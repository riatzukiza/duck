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
