import datetime
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

intents = discord.Intents.default()
client = discord.Client(intents=intents)
# litellm.set_verbose = True
sent_messages=set()


def valid_channel_choice(answer):
    """
    Check if answer is a valid channel choice.
    Checks "channel_name" as either an id or a name.
    Checks "channel_id" as either an id or a name.
    Checks "channel" as either an id or a name.
    """

    def either_name_or_id(key):
        try:
            answer_value=answer.get(key)
            print(answer_value)
            channel_by_name=get_channel_by_name(answer_value,client)
            channel_by_id=get_channel_by_id(answer_value,client)

            channel= channel_by_name or channel_by_id
            return channel
        except Exception as e:
            print("EXCEPTION in validating channel",e)
            return None
    return either_name_or_id("channel_name") or either_name_or_id("channel_id") or either_name_or_id("channel")
async def main():
    profile_docs=get_random_and_latest_messages(
        discord_message_collection, 
        user_id=settings.AUTHOR_ID,
        channel_id=settings.PROFILE_CHANNEL_ID,
        num_random=100,
        num_latest=100,
        num_user_docs=100
    )

    channel_choice=await ask_docs(
        f"Pick a channel from this list of channel names given the context: `{get_all_text_channels(client)}. Respond like this:{({'channel_name':'<channel_name>'})}", 
        docs=profile_docs,
        format="json",
        expires_in=random.randint(10,6000),
        check=valid_channel_choice,
        client=client
    )


    latest_channel_messages=get_random_and_latest_messages(
        discord_message_collection,
        channel_id=channel_choice.id,
        user_id=settings.AUTHOR_ID,
        num_random=10,
        num_latest=20,
        num_user_docs=100
    )
    for message in latest_channel_messages:
        print(f'{message["author_name"]} said "{message["content"]}" in {message["channel_name"]} at {message["created_at"]}')
    
    # # print("latest_channel_messages",latest_channel_messages)
    topics=await ask_doc_qa(
        "List all topics that were discussed.",
        docs=latest_channel_messages,
        format="string",
        client=client
    )
    purpose=await ask_doc_qa(
        "What is your purpose?",
        docs=latest_channel_messages,
        format="string",
        client     =client
    )
    summary=await ask_doc_qa(
        "What's going on in this channel?",
        docs=latest_channel_messages,
        format="string",
        client   =client
    )

    day_in_history=await ask_doc_qa(
        "What happened on this day in history?",
        docs=latest_channel_messages,
        format="string",
        client=client
    )

    twitch_coach=await ask_doc_qa(
        "How can I improve my twitch stream?",
        docs=latest_channel_messages,
        format="string",
        client=client
    )

    prompt_engineering=await ask_doc_qa(
        "What is the best way to engineer a prompt for the AI?",
        docs=latest_channel_messages,
        format="string",
        client=client
    )

    final_context=prompt_engineering+topics+purpose+summary+day_in_history+twitch_coach+get_context(
                    latest_channel_messages, 
                    client=client
                )

    content=await async_complete(
        final_context,
        temperature=0.9,
    )

    await send_message({
        "content":content,
        "channel":channel_choice.id
    },sent_messages,client,mark_sent=False)
    end_time=datetime.datetime.now()

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')
    await clear_answers(timmy_answer_cache_collection)
    while True:
        await main()





client.run(settings.DISCORD_TOKEN)
