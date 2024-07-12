import datetime
import json
import pymongo
import discord
import litellm
from litellm import completion
from litellm.llms.ollama import get_ollama_response
# from langchain_community.llms import Ollama
# from langchain.document_loaders import WebBaseLoader
# from langchain.text_splitter import RecursiveCharacterTextSplitter
# from langchain.embeddings import OllamaEmbeddings
# from langchain.vectorstores import Chroma
# from langchain.chats import Chat

from shared.data import CSVChunker
from shared.discord import get_latest_messages
from shared.mongodb import discord_message_collection

# ollama = Ollama(
#     base_url='http://localhost:11434',
#     model="llama3"
# )

# all_messages=discord_message_collection.find({}).sort(
#     "created_at",
#     pymongo.DESCENDING
# )

# data = CSVChunker(
#     name=f"unread_messages_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}",
#     cursor=all_messages,
#     chunk_size=100
# )


# text_splitter=RecursiveCharacterTextSplitter(chunk_size=100, chunk_overlap=15)
# all_splits = text_splitter.split_documents(data.chunks)


# oembed = OllamaEmbeddings(base_url="http://localhost:11434", model="nomic-embed-text")
# vectorstore = Chroma.from_documents(documents=all_splits, embedding=oembed)

# chat = Chat( ollama=ollama, vectorstore=vectorstore, text_splitter=text_splitter)


import discord
import pymongo
import asyncio

import shared.settings as settings
from shared.mongodb import generated_message_collection

intents = discord.Intents.default()
client = discord.Client(intents=intents)

async def send_message(message,sent_messages):
    """
    Send a message to the discord channel.
    """
    default_channel= client.get_channel(int(settings.DEFAULT_CHANNEL))
    if message not in sent_messages:
        await default_channel.send(message)
        sent_messages.add(message)
import requests

def pull_model(model):
    url = "http://ollama:11434/pull"  # Adjust the URL based on your API endpoint
    data = {
        "model": model
    }

    response = requests.post(url, json=data)

    if response.status_code == 200:
        print("Model pulled successfully.")
    else:
        print(f"Failed to pull model: {response.status_code} - {response.text}")

litellm.set_verbose = True

sent_messages=set()
def get_random_and_latest_messages(collection, user_id, num_random=5, num_latest=5):
    # Aggregation pipeline for random messages
    random_pipeline = [
        {"$sample": { "size": num_random } },
        {"$match": {"content":{
            "$not":{
                "$regex":r"(youtube.com|pplx.ai)","$options":"i"
            },
            "$nin":[None, "",".featured"]
        }}}
    ]

    # Aggregation pipeline for latest messages by a specific user
    user_docs_pipeline = [
        {"$match": {"user_id": user_id}},
        {"$sort": {"created_at": -1}},
        {"$limit": num_latest}
    ]

    latest_docs_pipeline = [
        {"$sort": {"created_at": -1}},
        {"$limit": num_latest}
    ]

    random_docs = list(collection.aggregate(random_pipeline))
    user_docs = list(collection.aggregate(user_docs_pipeline))
    latest_docs = list(collection.aggregate(latest_docs_pipeline))


    return random_docs, user_docs, latest_docs
@client.event
async def on_ready():
    print(f'Logged in as {client.user}')
    while True:
        try:
            random_docs,user_docs,latest_docs=get_random_and_latest_messages(
                discord_message_collection, 205909976768708608, num_random=30, num_latest=200
                )
            # Combine the two lists
            combined_docs = random_docs + latest_docs + user_docs

            # Sort the combined list by the 'created_at' field
            combined_docs.sort(key=lambda x: x['created_at'])

            # .sort(
            #     "created_at", pymongo.ASCENDING
            # ).limit(100).sort(
            #     "created_at", pymongo.DESCENDING
            # )
            # latetest_messages=CSVChunker(
            #     name=f"latest_messages_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}",
            #     cursor=,
            #     chunk_size=100
            # )
            context=[{"content":"""
                      You are a discord bot.
                      you are role playing a member of our community who is interested in video games, AI, and programming.
                      Your name is timmy.
                      I am Error.  I am the owner of the server.
                      You're another user in the discord channel.
                      mention a user with "@user_id" to send a message to them.

                      You will get some messages from our community. You will tell everyone why you are here.
                      you will ask questions about the messages you receive.
                        you will respond to the messages you receive.
                        you will ask questions about the messages you receive.
                        you will respond to the messages you receive.

                      
                      Errors messages are the most important.  Error is the owner of the server

                      Weeve together the messages you get into a single narative with out directly copying the messages.
                      gently guide the narative in a direction that is interesting to you.

                      Ask users about themselves.  Ask them about their interests.  Ask them about their projects.

                      Answer any questions that are asked of you if you can, or direct people to community members who can.
                      ""","role":"system"}]
            for message in combined_docs:
                context.append({
                    "content":f"""
                    channel_id:{message['channel']}
                    sent_at:({message['created_at']})
                    author_name:{message['author_name']}
                    author_id:{message['author']}
                    guild_id:{message['guild']}
                    raw_mentions:{message['raw_mentions']}
                    content:{message['content']}""",
                    "role":message['author_name'],
                })
            print("context",context)
            response_string=completion(
                model="ollama/llama3",
                messages=context,
                max_tokens=2000,
                api_base="http://ollama:11434"
            )
            await send_message(response_string.choices[0].message.content,sent_messages)
        except Exception as e:
            print("error:")
            print(e)    
        await asyncio.sleep(5)



client.run(settings.DISCORD_TOKEN)
