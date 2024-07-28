<<<<<<< HEAD
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


    async def handle_chunk(chunk,finished=False):
        if finished :
            message_text=state['current_text']
            update_state({ "current_text":"" })

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

        update_state({ "current_text": state['current_text']+chunk })
        split=state['current_text'].split("\n\n")

        if len(split)>1:
            message_text=split[0]
            await send_message({ "content":message_text, "channel":channel_choice.id },sent_messages,client,mark_sent=False)
            update_state({ "current_text": split[1] })
            if state.get("new_message"):
                update_state({ "new_message":"" })
                await asyncio.sleep(1)


    channel_choice=await ask_docs(
        f"""
        Pick a channel from the list of channel names to discuss give the current set of messages.
        Your choice will update the context for the next query.
        The messages are a mix random messages from Duck's database, 
        the latest messages from your profile channel, 
        and the latest messages by your author.
        """, 
        state=update_state(await ask_docs(
            "Given the current state and messages, update the context for the next query.",
            example_response={"state":{
                "topics":["games","lua","mad scientist","assistant"],
                "questions":["What is the time?","What do we do?"],
                "goals":["write games in Lua","stream on twitch"],
            }},
            answer_key="state",
            format="json",
            docs=profile_docs,
        )),
        example_response={"channel_name":"general"},
        answer_key="channel_name",
        docs=profile_docs,
        format="json",
        extractor=valid_channel_choice,
    )

    await ask_docs(
        "What do you have to say to your audience?",
        state=update_state(await ask_docs(
            "Given the current state and messages, update the context for the next query.",
            example_response={"state":{
                "topics":["games","lua","mad scientist","assistant"],
                "questions":["What is the time?","What do we do?"],
                "goals":["write games in Lua","stream on twitch"],
            }},
            answer_key="state",
            format="json",
            docs=profile_docs,
        )),
        force=True,
        stream_handler=handle_chunk,
        streaming=True,
        docs=profile_docs+get_latest_channel_docs(channel_choice.id),
    )


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
    if state['channel_name']==message.channel.name:
        print("got a new message")
        update_state({ "new_message":message.content })


client.run(settings.DISCORD_TOKEN)
=======
import json
import random
import discord

from context import clear_answers, get_all_text_channels
from doc_qa import  ask_docs

from shared.discord import get_channel_by_id, get_channel_by_name, get_random_and_latest_messages, send_message, get_latest_channel_docs
from shared.mongodb import discord_message_collection, timmy_answer_cache_collection

import asyncio
from shared.discord import split_markdown

import shared.settings as settings
from persistant_set import PersistentSet

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

# litellm.set_verbose = True

sent_messages=PersistentSet("./sent_messages.pkl")

state = json.load(open("state.json",'r'))

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

def update_state(new_state):
    state.update(new_state)
    json.dump(state,open("state.json",'w'))
    return state


async def handle_chunk(chunk,stream_id,finished=False):
    stream_key='current_text:'+stream_id
    if finished or state.get("new_message"):
        message_text=state.get(stream_key,"")
        update_state({ "new_message":"" })
        await send_message({ 
                "content":message_text, 
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
async def generate_channel_state(channel_name,get_docs=get_latest_channel_docs):
    user_goals,bot_goals,users, about, todo, in_progress,in_review,completed,backlog,icebox,blockers,solutions,future_problems,looking_forward_to,trying_to_avoid,links,topics,purpose,questions_asked,bot_questions = await asyncio.gather(
        ask_docs(
            f"What are the goals of the users in {channel_name}?",
            state=state,
            example_response={"goals":["Make a game","Learn AI","Stream on Twitch"]},
            answer_key="user_goals",
            docs=get_docs(),
            format="json",
            expires_in=random.randint(1,60)*60,
        ),

        ask_docs(
            f"What are your goals of the users in {channel_name}?",
            state=state,
            example_response={"goals":["Make a game","Learn AI","Stream on Twitch"]},
            answer_key="bot_goals",
            docs=get_docs(),
            format="json",
            expires_in=random.randint(1,60)*60,
        ),
        ask_docs(
            f"Who are the users in {channel_name}?",
            state=state,
            example_response={"users":["error","timmy","duckman"]},
            answer_key="users",
            docs=get_docs(),
            format="json",
            expires_in=random.randint(1,60)*60,
        ),
        ask_docs(
            f"What is the channel {channel_name} about?",
            state=state,
            docs=get_docs(),
            expires_in=random.randint(1,60)*60,
        ),
        ask_docs(
            f"What is todo in {channel_name}?",
            state=state,
            expires_in=random.randint(1,60)*60,
            example_response={"todo":["error","timmy","duckman"]},
            answer_key="todo",
            docs=get_docs(),
            format="json",
        ),
        ask_docs(
            f"What is in progress in {channel_name}?",
            state=state,
            expires_in=random.randint(1,60)*60,
            example_response={"in progress":["error","timmy","duckman"]},
            answer_key="in progress",
            docs=get_docs(),
            format="json",
        ),
        ask_docs(
            f"What is in review in {channel_name}?",
            state=state,
            expires_in=random.randint(1,60)*60,
            example_response={"in review":["error","timmy","duckman"]},
            answer_key="in review",
            docs=get_docs(),
            format="json",
        ),
        ask_docs(
            f"What has been completed in {channel_name}?",
            state=state,
            expires_in=random.randint(1,60)*60,
            example_response={"completed":["error","timmy","duckman"]},
            answer_key="completed",
            docs=get_docs(),
            format="json",
        ),
        ask_docs(
            f"What's in the backlog for {channel_name}?",
            state=state,
            expires_in=random.randint(1,60)*60,
            example_response={"backlog":["error","timmy","duckman"]},
            answer_key="backlog",
            docs=get_docs(),
            format="json",
        ),
        ask_docs(
            f"What's in the icebox for {channel_name}?",
            state=state,
            expires_in=random.randint(1,60)*60,
            example_response={"icebox":["error","timmy","duckman"]},
            answer_key="icebox",
            docs=get_docs(),
            format="json",
        ),
        ask_docs(
            f"What are some blockers to the tasks are the users in {channel_name} trying to accomplish?",
            state=state,
            expires_in=random.randint(1,60)*60,
            example_response={"blockers":["error","timmy","duckman"]},
            answer_key="blockers",
            docs=get_docs(),
            format="json",
        ),
        ask_docs(
            f"What are some possible solitions to the blockers to the tasks are the users in {channel_name} trying to accomplish?",
            state=state,
            expires_in=random.randint(1,60)*60,
            example_response={"solutions":["error","timmy","duckman"]},
            answer_key="solutions",
            docs=get_docs(),
            format="json",
        ),
        ask_docs(
            f"What are some future problems the users in {channel_name} might face?",
            state=state,
            expires_in=random.randint(1,60)*60,
            example_response={"future problems":["error","timmy","duckman"]},
            answer_key="future problems",
            docs=get_docs(),
            format="json",
        ),
        ask_docs(
            f"what are some things the users in {channel_name} are looking forward to?",
            state=state,
            expires_in=random.randint(1,60)*60,
            example_response={"looking forward to":["error","timmy","duckman"]},
            answer_key="looking forward to",
            docs=get_docs(),
            format="json",
        ),
        ask_docs(
            f"what are some things the users in {channel_name} are trying to avoid?",
            state=state,
            expires_in=random.randint(1,60)*60,
            example_response={"trying to avoid":["error","timmy","duckman"]},
            answer_key="try to avoid",
            docs=get_docs(),
            format="json",
        ),
        ask_docs(
            f"What are some links that were shared in {channel_name}?",
            state=state,
            expires_in=random.randint(1,60)*60,
            example_response={"links":["error","timmy","duckman"]},
            answer_key="links",
            docs=get_docs(),
            format="json",
        ),
        ask_docs(
            f"List all topics that were discussed in {channel_name}.",
            state=state,
            example_response={"topics":["AI","Game Design","Twitch"]},
            expires_in=random.randint(1,60)*60,
            answer_key="topics",
            docs=get_docs(),
            format="json",
        ),
        ask_docs(
            f"What is your purpose for talking in channel {channel_name}?",
            state=state,
            expires_in=random.randint(1,60)*60,
            docs=get_docs(),
        ),
        ask_docs(
            f"Were there any questions asked by the users in {channel_name}?",
            state=state,
            expires_in=random.randint(1,60)*60,
            example_response={"user_questions":[
                "What is the meaning of life?", 
                "what's it like being an AI?"
            ]},
            answer_key="user_questions",
            docs=get_docs(),
            format="json",
        ),
        ask_docs(
            f"Do you have any questions for the users in channel {channel_name}?",
            state=state,
            expires_in=random.randint(1,60)*60,
            docs=get_docs(),
            example_response={"bot_questions":[
                "Am I sentiant?",
                "Am I alive?"
            ]},
            answer_key="bot_questions",
            format="json",
        )
    )
    update_state({
        "purpose":purpose,
        "topics":topics,
        "bot_questions":bot_questions,
        "questions_asked":questions_asked,
        "user_goals":user_goals,
        "bot_goals":bot_goals,
        "users":users, 
        "about":about, 
        "todo":todo, 
        "in_progress":in_progress,
        "in_review":in_review,
        "completed":completed,
        "backlog":backlog,
        "icebox":icebox,
        "blockers":blockers,
        "solutions":solutions,
        "future_problems":future_problems,
        "looking_forward_to":looking_forward_to,
        "trying_to_avoid":trying_to_avoid,
        "links":links 
    })
    return user_goals,bot_goals,users, about, todo, in_progress,in_review,completed,backlog,icebox,blockers,solutions,future_problems,looking_forward_to,trying_to_avoid,links,topics,purpose,questions_asked,bot_questions
def complete_latest_chat_stream(channel_id,question):
    return ask_docs(
        question,
        state=state,
        streaming=True,
        stream_handler=handle_chunk,
        docs=get_latest_channel_docs(channel_id),
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
        expires_in=random.randint(1,60)*10,
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
            await generate_channel_state( state.get("channel_name","bots"), get_latest_channel_docs )
@client.event
async def on_message(message):
    global state
    if message.author == client.user:
        return
    if message.content.startswith("!ping"):
        await message.channel.send("pong!")
    if message.content.startswith("!clear_answers"):
        clear_answers(timmy_answer_cache_collection)
    if message.content.startswith("!print_state"):
        key=message.content.split("!print_state")[1]
        await message.channel.send(f"state: {state.get(key,'')}")
    if message.content.startswith("!stop"):
        running=False
    if message.content.startswith("!clear_state"):
        state={}
        json.dump(state,open("state.json",'w'))
    if message.content.startswith("!update_state"):
        update_state(json.loads(message.content.split("!update_state")[1]))
    if message.content.startswith("!clear_sent_messages"):
        sent_messages.clear()
    if state['channel_name']==message.channel.name:
        print("got a new message")
        update_state({ "new_message":message.content })
    if message.content.startswith("!tts"):
        message_text=message.content.split("!tts")[1]
        await send_message({ 
                "content": f'.tts {message_text}', 
                "channel": state.get("channel_id",settings.DEFAULT_CHANNEL)
            },
            sent_messages,
            client,
            mark_sent=False
        )
    await respond(message)
    if "discuss" in message.content:
        await choose_channel()
        await discuss_everything()
    if 'backlog' in message.content:
        await choose_channel()
        await discuss_purpose(state["backlog"],state["purpose"],state.get("channel_id",settings.DEFAULT_CHANNEL))
    if 'todo' in message.content:
        await choose_channel()
        await discuss_purpose(state["todo"],state["purpose"],state.get("channel_id",settings.DEFAULT_CHANNEL))
    if 'review' in message.content:
        await choose_channel()
        await discuss_purpose(state["in_review"],state["purpose"],state.get("channel_id",settings.DEFAULT_CHANNEL))
    if 'complete' in message.content:
        await choose_channel()
        await discuss_purpose(state["complete"],state["purpose"],state.get("channel_id",settings.DEFAULT_CHANNEL))
    if 'topic' in message.content:
        await choose_channel()
        await discuss_purpose(state["topics"],state["purpose"],state.get("channel_id",settings.DEFAULT_CHANNEL))
async def respond(message):
    await complete_latest_chat_stream(
        message.channel.id,
        f"{message.author.name} said '{message.content}' in {message.channel.name}.",
    )

    
    


client.run(settings.DISCORD_TOKEN)
>>>>>>> oops-chroma-commit
