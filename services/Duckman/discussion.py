import random

from shared import settings
from state import update_state,state
from shared.discord import send_message, split_markdown
from sent_messages import sent_messages

from shared.discord import get_channel_by_id, get_channel_by_name, get_latest_channel_docs
from shared.discord_text_splitter import split_markdown
from shared.doc_qa import ask_docs
from shared.embeddings import generate_embedding
from shared.mongodb import discord_message_collection
from context import  get_all_text_channels
from discord_client import client
import chromadb

search_collection = chromadb.PersistentClient(path="./chroma_db").get_or_create_collection(name="search_results")

def get_documents_by_ids(ids): return list(discord_message_collection.find({'_id': {'$in': ids}}).sort([("created_at", -1)]))

async def respond_to_state(message):
    # use vision model if message has image.

    return await complete_latest_chat_stream(
        message.channel.id,
        f"{message.author.name.replace('[Scriptly] ','(Transcribed)')} said '{message.content}' in {message.channel.name}.",
    )

async def complete_latest_chat_stream(channel_id,question,key="last_user_question",image=None):
    update_state({ "channel_id":channel_id })

    # for now load the client in the function so the context is as fresh as possible.
    
    chroma_client = chromadb.PersistentClient(path="./chroma_db")

    file_chroma = chroma_client.get_or_create_collection(name="duckman_files")
    message_chroma = chroma_client.get_or_create_collection(name="discord_messages")
    search_chroma = chroma_client.get_or_create_collection(name="search-results")

    question_embedding = await generate_embedding(question)

    results = get_documents_by_ids(message_chroma.query(
        query_embeddings=[question_embedding], n_results=200)['ids'][0])
    relavent_files= file_chroma.query(
        query_embeddings=[question_embedding], n_results=20)['documents'][0]
    search_results= search_chroma.query(
        query_embeddings=[question_embedding], n_results=20)['documents'][0]

    profile_docs=get_latest_channel_docs(settings.PROFILE_CHANNEL_ID)
    unique_docs=set()
    def is_unique_document(doc): 
        if doc['_id'] in unique_docs:
            return False
        else:
            unique_docs.add(doc['_id'])
            return True

    docs=list(filter(is_unique_document,  get_latest_channel_docs(channel_id)+profile_docs+results))

    # sort by time newest last
    docs.sort(key=lambda x: x['created_at'])

    async def handle_chunk(chunk,stream_id,finished=False):
        stream_key='current_text:'+stream_id
        if finished or state.get("new_message","")!="":
            split=split_markdown(state.get(stream_key,""),finished=True)
            update_state({ "new_message":"" })
            await send_message({ 
                    "content":split[0], 
                    "channel": state.get("channel_id",settings.DEFAULT_CHANNEL)
                },
                sent_messages,
                client,
                mark_sent=False
            )
            return chunk
        update_state({ stream_key: state.get(stream_key,"")+chunk })

        split=split_markdown(state.get(stream_key,""))

        if len(split)>1:
            await send_message({ "content":split[0], "channel":state['channel_id'] },sent_messages,client,mark_sent=False)
            update_state({ stream_key: "".join(split[1:]) })
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

async def choose_channel(profile_docs=get_latest_channel_docs(settings.PROFILE_CHANNEL_ID)):
    channel=await ask_docs(
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
        expires_in=random.randint(1,60)*60,
        example_response={"channel_name":"bots"},
        answer_key="channel_name",
        docs=profile_docs,
        format="json",
        extractor=valid_channel_choice,
    )
    update_state({ "channel_name":channel.name , "channel_id":channel.id  })
    return channel