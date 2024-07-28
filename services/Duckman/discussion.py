import asyncio
import random
from shared import settings
from shared.discord import get_channel_by_id, get_channel_by_name, get_latest_channel_docs
from shared.doc_qa import ask_docs
from shared.mongodb import discord_message_collection
from shared.create_message_embeddings import chroma_collection
from state import generate_state_property_update, update_state, update_state_from_search, state
from context import clear_answers, get_all_text_channels
from discord_client import client
from handle_chunk import handle_chunk
import chromadb

search_collection = chromadb.PersistentClient(path="./chroma_db").get_or_create_collection(name="search_results")

def get_documents_by_ids(ids):
    # Connect to MongoDB

    # Convert string IDs to ObjectId

    # Query to find documents with the specified IDs
    documents = discord_message_collection.find({'_id': {'$in': ids}}).sort([("created_at", -1)])

    # Convert the cursor to a list
    document_list = list(documents)
    
    return document_list
async def respond_to_state(message):
    return await complete_latest_chat_stream(
        message.channel.id,
        f"{message.author.name.replace('[Scriptly] ','(Transcribed)')} said '{message.content}' in {message.channel.name}.",
    )

async def complete_latest_chat_stream(channel_id,question,key="last_user_question"):
    update_state({ "channel_id":channel_id })

    results = get_documents_by_ids(chroma_collection.query(query_texts=[question], n_results=200)['ids'][0])
    search_results= search_collection.query(query_texts=[question], n_results=200)['documents'][0]
    # print("search results",search_results)
    profile_docs=get_latest_channel_docs(settings.PROFILE_CHANNEL_ID)
    docs=get_latest_channel_docs(channel_id)+results+profile_docs

    # sort by time newest last
    docs.sort(key=lambda x: x['created_at'])

    return await ask_docs( 
        question, state=state, streaming=True, docs=docs, 
        stream_handler=handle_chunk, 
        search_results=search_results
    )


def discuss_topic_relationships(t1,t2,channel_id):
    return asyncio.gather(*[complete_latest_chat_stream(
        channel_id,
        f"Discuss '{_topic1}' as it relates to '{_topic2}'.",
    ) for _topic1 in t1 for _topic2 in t2])

def discuss_purpose(topics,purpose,channel_id):
    return asyncio.gather(*[complete_latest_chat_stream(
        channel_id,
        f"Discuss '{topic}' as it relates to '{purpose}'.",
    ) for topic in topics]) 

def answer_questions(questions,subject):
    return asyncio.gather(*[complete_latest_chat_stream(
        state.get("channel_id",settings.DEFAULT_CHANNEL),
        f"Answer '{question}' as it relates to '{subject}' for channel {state.get('channel_name','general')}.",
    ) for question in questions])




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

async def generate_channel_state(channel_name):
    return await asyncio.gather(
        generate_state_property_update(
            f"What are your goals of the users in {channel_name}?",
            example={"bot_goals":["Make a game","Learn AI","Stream on Twitch"]},
            key="bot_goals",
        ),
        generate_state_property_update(
            f"Who are the users in {channel_name}?",
            example=["error","timmy","duckman"],
            key="users"
        ),
        generate_state_property_update(
            f"What is your current focus?",
            example="Thinking about what to do next?",
            key="focus"
        ),
        generate_state_property_update(
            f"What is the channel {channel_name} about?",
            example="This channel is about making games.",
            key="about",
        ),
        generate_state_property_update(
            f"What is todo in {channel_name}?",
            example=["Make a game","Learn AI","Stream on Twitch"],
            key="todo",
        ),
        generate_state_property_update(
            f"What is in progress in {channel_name}?",
            example=["Design game","Write AI","Prepare for stream"],
            key="in_progress",
        ),
        generate_state_property_update(
            f"What is in review in {channel_name}?",
            example=["Bot response protocol","AI training","Game design"],
            key="in_review",
        ),
        generate_state_property_update(
            f"What has been completed in {channel_name}?",
            example=["Chat bot","Learn love2d","Stream on Twitch about mega duck"],
            key="completed",
        ),
        generate_state_property_update(
            f"What's in the backlog for {channel_name}?",
            example=["Make a website for duck", "Write a book about ducks", "Make a game about ducks","Better twitch profile"],
            key="backlog",
        ),
        generate_state_property_update(
            f"What are some blockers to the tasks are the users in {channel_name} trying to accomplish?",
            example=["Bot talks too fast","Bot talks too slow","Bot talks too much"],
            key="blockers",
        ),
        generate_state_property_update(
            f"What are some links that were shared in {channel_name}?",
            example=["http://google.com","http://github.com","http://twitch.tv"],
            key="http_links_shared",
        ),
        generate_state_property_update(
            f"List all topics that were discussed in {channel_name}.",
            example=["games","lua","mad scientist","assistant"],
            key="topics",
        ),
        generate_state_property_update(
            f"What is your purpose for talking in channel {channel_name}?",
            example="You pass butter.",
            key="purpose",
        ),
        generate_state_property_update(
            f"Were there any questions asked by the users in {channel_name}?",
            example=["How do I make a game?","How do I write better AI prompts?","What is duck doing?"],
            key="user_questions",
        ),
        generate_state_property_update(
            f"Do you have any questions for the users in channel {channel_name}?",
            example=["What are you working on?","What are you looking forward to?","What are you trying to avoid?"],
            key="bot_questions",
        )
    )
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
async def discuss_everything():

    profile_docs=get_latest_channel_docs(settings.PROFILE_CHANNEL_ID)
    print("profile docs",len(profile_docs))

    channel_choice=await choose_channel(profile_docs)
    await generate_channel_state( channel_choice.name, get_latest_channel_docs )

    await answer_questions(state["bot_questions"],state["purpose"])
    await answer_questions(state["questions_asked"],state["purpose"])
    await discuss_purpose(state["topics"],state["purpose"],channel_choice.id)
    await generate_channel_state( channel_choice.name, get_latest_channel_docs )
    await discuss_topic_relationships(state["complete"],state["in review"],channel_choice.id)
    await discuss_topic_relationships(state["in_review"],state["in_progress"],channel_choice.id)
    await discuss_topic_relationships(state["in_progress"],state["todo"],channel_choice.id)
    await discuss_topic_relationships(state["todo"],state["backlog"],channel_choice.id)
    await discuss_topic_relationships(state["backlog"],state["icebox"],channel_choice.id)
    await discuss_topic_relationships(state["in_pgoress"],state["blockers"],channel_choice.id)
    await discuss_topic_relationships(state["in_review"],state["blockers"],channel_choice.id)
    await discuss_topic_relationships(state["todo"],state["blockers"],channel_choice.id)
    await discuss_topic_relationships(state["backlog"],state["blockers"],channel_choice.id)
    await discuss_topic_relationships(state["user_goals"],state["future_problems"],channel_choice.id)
    await discuss_topic_relationships(state["user_goals"],state["looking_forward_to"],channel_choice.id)

    await complete_latest_chat_stream(
        channel_choice.id,
        "What do you have to say to your audience?",
    )