"""
A small library for interating with the discord api
"""
import asyncio
import random
import pymongo
import pandas as pd
import discord
from shared import settings
from shared.mongodb import discord_message_collection, generated_message_collection
from shared.wiki import crawl, get_wikipedia_chunks

CONTENT_FILTER=[
    {"content":{"$nin":[None, "",".featured"]}},
    {"content":{"$not":{"$regex":r"(youtube.com|pplx.ai)","$options":"i"}}}
]

TRAIN_AUTHOR_FILTER={
    "$not":{"$regex":r"roarar","$options":"i"},
    "$nin":[None,"","Duck","Roarar"]
}

GEN_AUTHOR_FILTER={
    "$nin":[None,"","Roarar"]
}


def get_unread_messages( limit=20):
    """
    Retrieve messages where the 'read' field is either false or undefined, 
    excluding specified fields, and return them as a pandas DataFrame.

    Args:
        collection (pymongo.collection.Collection): The MongoDB collection to retrieve messages from.
        limit (int): The number of messages to retrieve.

    Returns:
        pd.DataFrame: DataFrame containing the messages.
    """
    query = {
        "$or": [
            {"read": False},
            {"read": {"$exists": False}}
        ],
        "$and":CONTENT_FILTER,
        "content":CONTENT_FILTER,
        "author_name": TRAIN_AUTHOR_FILTER
    }
    return discord_message_collection.find(query).sort("created_at", pymongo.ASCENDING).limit(limit)

def mark_as_read(message):
    """
    Mark a message as read.
    """
    print("marrking as read", message["_id"])
    discord_message_collection.update_one(
        {"_id": message["_id"]},
        {"$set": { "read": True, "readCount": message['readCount'] + 1 if 'readCount' in message else 1}}
    )

def mark_messages_as_read(messages):
    """
    Mark a list of messages as read.
    """
    for message in messages:
        mark_as_read(message)

def get_latest_messages(n=10):
    """
    Get the latest messages from the discord channel.
    """
    return discord_message_collection.find({
        "$and":CONTENT_FILTER,
        "author_name":GEN_AUTHOR_FILTER
    }).sort(
        "created_at", pymongo.DESCENDING
    ).limit(n)


def get_random_unique_messages(n=10):
    """
    Get a unique random selection of messages from the discord channel.
    """
    return discord_message_collection.aggregate([
        { "$sample": { "size": n } },
        { "$sort": { "created_at": 1 } },
        # Remove duplciates
        # https://stackoverflow.com/questions/37977434/mongodb-aggregate-remove-duplicates
        # What? This is a hack. Why is this necessary?
        # This is necessary because the $sample stage does not guarantee unique results.
        # The $group stage is used to remove duplicates.
        # The $first accumulator is used to keep the first document in each group.
        # The $replaceRoot stage is used to promote the document to the root level.
        # This is necessary because the $group stage adds an _id field to the document.
        { "$group": { "_id": "$_id", "doc": { "$first": "$$ROOT" } } },
        { "$replaceRoot": { "newRoot": "$doc" } }

    ])

def get_read_messages(n=10):
    """
    Get the latest read messages from the discord channel.
    """
    return discord_message_collection.find({
        "read": True,
        "content":CONTENT_FILTER,
        "author_name":TRAIN_AUTHOR_FILTER
    }).sort(
        "created_at", pymongo.DESCENDING
    ).limit(n)

def get_unsent_messages():
    """
    Get messages the model has not yet sent.
    """
    return generated_message_collection.find({
        "sent": False
    }).sort([("created_at", 1)])

async def help_commands(message):
    if message.content.startswith('!help'):
        await message.channel.send('Commands: !hello, !goodbye, !ping, !pong, !help, !wiki <query>, !random, !roll, !coinflip, !dice, !8ball')
    if message.content == '.help':
        await message.channel.send(
            """
            .count_unsent - Count unsent messages
            .count_all - Count all messages
            .count_channel_messages - Count messages in the current channel
            .count_user_messages - Count messages by the current user
            .clear - Clear unsent messages
            .list_servers - List servers
            .list_channels - List channels
            !hello - Say hello
            !goodbye - Say goodbye
            !ping - Ping
            !pong - Pong
            !help - Show help
            !wiki <query> - Search Wikipedia
            !random - Generate a random number
            !roll - Roll a dice
            !coinflip - Flip a coin
            !dice - Roll a dice
            !8ball - Ask the magic 8-ball
            !crawl <query> - Crawl Wikipedia
            
            """,
            tts=True
        )
async def count_commands(message):
    if message.content == '.count_unsent':
        unsent_messages = list(get_unsent_messages())
        await message.channel.send(f'Unsent messages: {len(unsent_messages)}',tts=True)
    if message.content == '.count_all':
        all_messages = list(discord_message_collection.find())
        await message.channel.send(f'All messages: {len(all_messages)}',tts=True) 

    if message.content == '.count_channel_messages':
        channel_messages = generated_message_collection.find({
            "channel": message.channel.id
        })
        await message.channel.send(f'Channel messages: {channel_messages.count()}',tts=True)
    if message.content == '.count_user_messages':
        user_messages = generated_message_collection.find({
            "author_name": message.author.name
        })
        await message.channel.send(f'User messages: {user_messages.count()}')
async def list_commands(message,client):
    if message.content == '.list_servers':
        for guild in client.guilds:
            await message.channel.send(guild.name)

    if message.content == '.list_channels':
        await message.channel.send("These are all the guilds I can see.",tts=True)
        for guild in client.guilds:
            await message.channel.send(f"In the guild {guild.name} I see the following categories:",tts=True)
            for category in guild.categories:
                await message.channel.send(f"In the category {category.name} in {guild.name} I see the following channels:",tts=True)
                for channel in category.channels:
                    channel_messages=list(discord_message_collection.find({"channel":channel.id}))
                    await message.channel.send(f"In the channel {channel.name} in the category {category.name} in the guild {guild.name} there are {len(channel_messages)} messages.",tts=True)

async def basic_commands(message):

    if message.content.startswith('!hello'):
        await message.channel.send('Hello!')
    if message.content.startswith('!goodbye'):
        await message.channel.send('Goodbye!')
    if message.content.startswith('!ping'):
        await message.channel.send('Pong!')
    if message.content.startswith('!pong'):
        await message.channel.send('Ping!')
    if message.content.startswith('!random'):
        random_number = random.randint(1, 100)
        await message.channel.send(f'Random number: {random_number}')
    if message.content.startswith('!roll'):
        roll_result = random.randint(1, 6)
        await message.channel.send(f'You rolled a {roll_result}!')
    if message.content.startswith('!coinflip'):
        coin = random.choice(['Heads', 'Tails'])
        await message.channel.send(f'You flipped a coin and got: {coin}')
    if message.content.startswith('!dice'):
        dice_result = random.randint(1, 6)
        await message.channel.send(f'You rolled a {dice_result} on the dice!')
    if message.content.startswith('!8ball'):
        responses = [
            'It is certain.',
            'It is decidedly so.',
            'Without a doubt.',
            'Yes – definitely.',
            'You may rely on it.',
            'As I see it, yes.',
            'Most likely.',
            'Outlook good.',
            'Yes.',
            'Signs point to yes.',
            'Reply hazy, try again.',
            'Ask again later.',
            'Better not tell you now.',
            'Cannot predict now.',
            'Concentrate and ask again.',
            'Don\'t count on it.',
            'My reply is no.',
            'My sources say no.',
            'Outlook not so good.',
            'Very doubtful.'
        ]
        response = random.choice(responses)
        await message.channel.send(f'🎱 {response}')

async def clear_command(message):
    if message.content == '.clear':
        await message.channel.send("Clearing unsent messages",tts=True)
        unsent_messages = list(get_unsent_messages())
        print(f'clearing {len(unsent_messages)} unsent messages')
        await message.channel.send(f'clearing {len(unsent_messages)} unsent messages',tts=True)
        generated_message_collection.update_many(
            {"sent": False},
            {"$set": { "sent": True}}
        )
        print("Cleared unsent messages")
        await message.channel.send("Cleared unsent messages",tts=True)

async def wiki_commands(message):
    if message.content.startswith('!crawl'):
        search_query = message.content[7:]
        await crawl(search_query,message)
    if message.content.startswith('!wiki'):
        search_query = message.content[6:]
        chunks = get_wikipedia_chunks(search_query)
        channel = message.channel
        for chunk in chunks:
            await channel.send(chunk)
            await asyncio.sleep(random.randint(1, 2))

async def all_commands(message,client):
    if message.author == client.user:
        return
    await clear_command(message)
    await wiki_commands(message)
    await basic_commands(message)
    await list_commands(message,client)
    await count_commands(message)
    await help_commands(message)

async def send_message(message, sent_messages,client,mark_sent=True):
    """
    Send a message to the discord channel.
    """
    if mark_sent:
        generated_message_collection.update_one(
            {"_id": message["_id"]},
            {"$set": {"sent": True}}
        )

    try:
        print("Trying to send", message['content'], "to", message['channel'])
        channel = client.get_channel(int(message['channel']))
    except Exception:
        print("Failed to get generated channel. Using default channel.")
        channel = client.get_channel(int(settings.DEFAULT_CHANNEL))

    message_key = f"{str(message['channel'])}:{message['content']}"
    if message_key in sent_messages:
        print("Message already sent:", message)
        return

    sent_messages.add(message_key)


    sentences = message['content'].split("\n")
    for sentence in sentences:
        if sentence.strip() and f"{message['channel']}:{sentence}" not in sent_messages:
            await asyncio.sleep(random.randint(1, 2))
            try:
                print("Sending message:", sentence, "to", channel.name)
                sent_messages.add(f"{message['channel']}:{sentence}")
                await channel.send(sentence, tts=True)
            except Exception:
                print("Failed to send to generated channel. Using default channel.")
                channel = client.get_channel(int(settings.DEFAULT_CHANNEL))
                await channel.send(sentence, tts=True)

def get_random_and_latest_messages(collection, user_id, channel_id, num_user_docs=100, num_random=5, num_latest=5):
    # Common match criteria
    common_match = {
        "content": {"$not": {"$regex": r"(youtube.com|pplx.ai)", "$options": "i"}, "$nin": [None, "", ".featured"]},
        "author_name": {"$nin": [None, "", "Roarar"]},
        "author": {"$nin": [user_id]}
    }

    # Aggregation pipeline for random messages
    random_pipeline = [
        {"$sample": {"size": num_random}},
        {"$match": common_match}
    ]

    # Aggregation pipeline for latest messages by a specific user
    user_docs_pipeline = [
        {"$match": {"user_id": user_id}},
        {"$sort": {"created_at": -1}},
        {"$limit": num_user_docs}
    ]

    # Aggregation pipeline for latest messages in a specific channel
    channel_docs_pipeline = [
        {"$match": {"channel": channel_id}},
        {"$sort": {"created_at": -1}}
    ]

    # Aggregation pipeline for latest messages
    latest_docs_pipeline = [
        {"$match": common_match},
        {"$sort": {"created_at": -1}},
        {"$limit": num_latest}
    ]

    random_docs = list(collection.aggregate(random_pipeline))
    user_docs = list(collection.aggregate(user_docs_pipeline))
    latest_docs = list(collection.aggregate(latest_docs_pipeline))
    channel_docs = list(collection.aggregate(channel_docs_pipeline))

    combined_docs = random_docs + latest_docs + user_docs + channel_docs
    combined_docs.sort(key=lambda x: x['created_at'])
    return combined_docs

def get_channel_by_name(name,client):
    """Get a discord channel by name from the discord client.

    Args: name (str): The name of the discord channel.
    """
    return discord.utils.get(client.get_all_channels(), name=name)
def get_channel_by_id(id,client):
    """Get a discord channel by id from the discord client.

    Args: id (int): The id of the discord channel.
    """
    return client.get_channel(id)
    