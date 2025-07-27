import random

from shared import settings
from state import update_state,state
from shared.discord import send_message
from sent_messages import sent_messages

from shared.discord import get_channel_by_id, get_channel_by_name, get_latest_channel_docs
from shared.discord_text_splitter import DiscordTextSplitter
from shared.doc_qa import ask_docs
from shared.mongodb import discord_message_collection
from context import  get_all_text_channels
from discord_client import client
from shared.doc_store import get_documents
import chromadb


chroma_client = chromadb.PersistentClient(path="./chroma_db")

file_chroma = chroma_client.get_or_create_collection(name="duckman_files")
message_chroma = chroma_client.get_or_create_collection(name="discord_messages")
search_chroma = chroma_client.get_or_create_collection(name="search-results")

def get_documents_by_ids(ids): return list(discord_message_collection.find({'_id': {'$in': ids}}).sort([("created_at", -1)]))

async def respond_to_state(message):
    # use vision model if message has image.

    return await complete_latest_chat_stream(
        message.channel.id,
        f"{message.author.name.replace('[Scriptly] ','(Transcribed)')} said '{message.content}' in {message.channel.name}.",
    )

async def complete_latest_chat_stream(channel_id,question):
    update_state({ "channel_id":channel_id })
    docs, search_results, relavent_files = await get_documents(question, channel_id)

    splitter=DiscordTextSplitter(max_length=2000)

    async def handle_chunk(chunk,stream_id,finished=False):
        if finished or state.get("new_message","")!="":
            update_state({ "new_message":"" })
            await send_message({
                    # The stream is over, just send whatever was left.
                    "content":splitter.current_chunk,
                    "channel": state.get("channel_id",settings.DEFAULT_CHANNEL)
                },
                sent_messages,
                client,
                mark_sent=False
            )
            return chunk

        maybe_message=splitter.add_token(chunk)

        if maybe_message is not None:
            await send_message({
                "content":maybe_message,
                "channel":state['channel_id']
            }, sent_messages,client,mark_sent=False)
    return await ask_docs(
        question, streaming=True, docs=docs,
        stream_handler=handle_chunk,
        search_results=search_results,
        relavent_files=relavent_files
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
