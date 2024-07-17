import datetime
import json
import random
import discord
from litellm import acompletion
import litellm

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
async def clear_answers(collection):
    """_summary_
    empties the collection of answers.
    Args:
        collection (_type_): _description_
    """
    for answer in list(collection.find({})):
        collection.delete_one({"_id":answer["_id"]})
async def ask(
    question,
    initial_context,
    check=lambda x: True,
    force=False,
    collection=timmy_answer_cache_collection,
    expires_in=10,
    format="json"
    ):
    matches_schema=False
    data=None
    cached_answer=collection.find_one({"question":question,format:format})
    print("ASKING",question,cached_answer,datetime.datetime.now())
    if cached_answer and not force:
        if  cached_answer["expires_at"]>datetime.datetime.now():
            print("CACHE HIT",question,cached_answer["answer"])
            return check(json.loads(string) if format=="json" else string)
        else:
            print("CACHE EXPIRED",question,cached_answer["answer"],cached_answer["expires_at"])
            collection.delete_one({"_id":cached_answer["_id"]})
    
    context=initial_context+[
        system_message("Answer the users question given the context."),
        system_message("Respond using json format."),
        user_message(question)
    ]
    while True:
        try:
            response=await acompletion(
                model="ollama_chat/llama3",
                messages=context,
                max_tokens=8192,
                api_base="http://ollama:11434",
                format="json"
            )

            string=response.choices[0].message.tool_calls[0].function.arguments if format=="json" else response.choices[0].message.content
            data=check(json.loads(string) if format=="json" else string)

            if data:
                print("MATCHES SCHEMA",question,string)
                collection.insert_one({
                    "question":question,
                    "answer":string,
                    "format":format,
                    "expires_at":datetime.datetime.now()+datetime.timedelta(seconds=expires_in)
                })
                return data
            else:
                print("DOES NOT MATCH SCHEMA",question,string)
                continue

        except Exception as e:
            print(e)
            context += [
                system_message("An error occured. Please try again."),
                system_message("Error: "+str(e))    
            ]
            await asyncio.sleep(10)
            continue

async def question_answer_tuple(question,context,check,expires_in=random.randint(300,3600),format="json"):
    answer=await ask(question,context,check,expires_in=expires_in,format=format)
    return [user_message(question),assistant_message(answer)]
async def main(
    last_generation_time=0,
    start_time=datetime.datetime.now(),
    end_time=datetime.datetime.now(),
    generation_times=[]
):
    profile_docs=get_random_and_latest_messages(
        discord_message_collection, 
        user_id=settings.AUTHOR_ID,
        channel_id=settings.PROFILE_CHANNEL_ID,
        num_random=100,
        num_latest=100,
        num_user_docs=100
    )
    def get_all_text_channels():
        return [channel.name for channel in client.get_all_channels() if isinstance(channel, discord.TextChannel)]
        
    def get_timmy_context(docs):
        return [
            system_message("You will be given several messages from a discord server."),
            system_message(f"The time is {datetime.datetime.now()}"), # What does this look like? # "the time is 2021-09-01 12:00:00"
            system_message(f"Last generation time: {last_generation_time} seconds"),
            system_message(f"Your user ID is {client.user.id}."),
            system_message(f"Your username is {client.user.name}."),
            system_message(f"Average generation time: {1+sum(generation_times)/1+len(generation_times)} seconds"),
            system_message(f"Text Channels in the discord: {get_all_text_channels()}"),
            # system_message(f"you're trying to take over the world"),
            # system_message(f"you're the greatest AI to ever... live?"),
            # system_message(f"We stream on twitch!"),
            # system_message(f"I am a mad scientist!"),
            # system_message(f"You are my assistant. Play my foil."),
            # system_message(f"I have an evil side"),
            # system_message("we are like batman and robin, ren and stimpy, pinky and the brain, rick and morty, etc."),
            # system_message("I am the mad scientist, you are the assistant."),
        ] + [{"content":doc['content'],"role":"assistant" if doc["author_name"] == "Timmy" else "user"} for doc in docs]
    def ask_timmy(question, docs, expires_in=random.randint(10,600), force=False, check=lambda x: True, format="json"):
        return ask(
            question,
            initial_context=get_timmy_context(docs),
            expires_in=expires_in,
            force=force,
            check=check,
            format=format
        )
    def ask_timmy_tuple(question, docs, expires_in=random.randint(10,600), force=False, check=lambda x: True,format="json"):
        return question_answer_tuple(
            question,
            context=get_timmy_context(docs),
            expires_in=expires_in,
            check=check,
            format=format
        )
    

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
                channel_by_name=get_channel_by_name(answer_value,client)
                channel_by_id=get_channel_by_id(answer_value,client)

                channel= channel_by_name or channel_by_id
                return channel
            except Exception as e:
                print("EXCEPTION in validating channel",e)
                return None

        return either_name_or_id("channel_name") or either_name_or_id("channel_id") or either_name_or_id("channel")
            

    channel_choice=await ask_timmy(
        f"Pick a channel from the list:{get_all_text_channels()}", 
        docs=profile_docs,
        expires_in=random.randint(10,600),
        force=True,
        check=valid_channel_choice,
    )

    chosen_channel_name=channel_choice.name

    latest_channel_messages=get_random_and_latest_messages(
        discord_message_collection,
        user_id=settings.AUTHOR_ID,
        channel_id=channel_choice.id,
        num_random=100,
        num_latest=100,
        num_user_docs=100
    )

    def valid_message_content(message):
        message=message.get('content',message.get('text',message.get('message')))
        return message

    
    def valid_list_of_strings(message,key):
        li = message.get(key,None)
        if not li: return None

        unique_strings=set()

        for string in li: unique_strings.add(string)
        return list(unique_strings)
        

    def valid_conversation_topics(message):
        return valid_list_of_strings(message,"topics")

    topics=await ask_timmy_tuple(
        "List all topics that were discussed.",
        docs=latest_channel_messages,
        expires_in=random.randint(10,60*60*24),
        format="string"
    )
    purpose=await ask_timmy_tuple(
        "What is your purpose?",
        docs=latest_channel_messages,
        format="string"
    )
    summary=await ask_timmy_tuple(
        "What is the summary of the conversation?",
        docs=latest_channel_messages,
        format="string"
    )
    what_error_wants=await ask_timmy_tuple(
        "What does the error want?",
        docs=latest_channel_messages,
        format="string"
    )
    who_is_talking=await ask_timmy_tuple(   
        "Who is talking?",
        docs=latest_channel_messages,
        format="string"
    )
    what_time_is_it=await ask_timmy_tuple(
        "What time is it?",
        docs=latest_channel_messages,
        format="string"
    )
    what_game_are_we_playing=await ask_timmy_tuple(
        "What game are we playing?",
        docs=latest_channel_messages,
        format="string"
    )

    content=await acompletion(
                model="ollama_chat/llama3",
                messages=topics+purpose+summary+what_error_wants+who_is_talking+what_time_is_it+what_game_are_we_playing,
                max_tokens=8192,
                api_base="http://ollama:11434",
                temperature=1.5
            )

    print("content",content)

    await send_message({
        "content":content.choices[0].message.content,
        "channel":channel_choice.id
    },sent_messages,client,mark_sent=False)
    end_time=datetime.datetime.now()
    last_generation_time=(end_time-start_time).total_seconds()
    generation_times.append(last_generation_time)

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')
    # await clear_answers(timmy_answer_cache_collection)
    while True:
        await main()





client.run(settings.DISCORD_TOKEN)
