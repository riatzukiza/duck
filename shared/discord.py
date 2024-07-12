"""
A small library for interating with the discord api
"""
import pymongo
import pandas as pd
from shared.mongodb import discord_message_collection
from shared.data  import FIELDS_TO_EXCLUDE
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
