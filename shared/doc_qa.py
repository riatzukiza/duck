
import asyncio
import datetime
import random
from shared.data import assistant_message, system_message, user_message
from shared.completion import async_complete

import traceback

from context import get_context     
from shared.mongodb import timmy_answer_cache_collection

def ask_docs(
    question, 
    docs,
    provider="http://ollama-gpu:11434",
    expires_in=random.randint(120,60000), 
    force=False, 
    extractor=lambda x: x, 
    stream_handler=None,
    streaming=False,
    example_response={"result":"This is an example response."},
    answer_key="result",
    format=None,
    search_results=[],
    relavent_files=[],
    ):
    return ask_context(
        question,
        provider=provider,
        initial_context=get_context(docs,search_results,relavent_files),
        expires_in=expires_in,
        example_response=example_response,
        answer_key=answer_key,
        force=force,
        stream_handler=stream_handler,
        streaming=streaming,
        extractor=extractor,
        format=format
    )

async def ask_context(
    question,
    initial_context,
    provider="http://ollama-gpu:11434",
    example_response={"result":"This is an example response."},
    answer_key="result",
    extractor=lambda x: x, # Extracts the object we want from the data we get back.
    force=False,
    stream_handler=None,
    streaming=False,
    collection=timmy_answer_cache_collection,
    expires_in=60000,
    format=None
    ):

    cached_answer=collection.find_one({"question":question,"format":format})
    print("question",datetime.datetime.now())
    print(question)

    if cached_answer and not force:
        if  cached_answer["expires_at"]>datetime.datetime.now():
            print("cached",datetime.datetime.now())
            print(cached_answer['answer'])
            return extractor(cached_answer['answer'][answer_key] if format=="json" else cached_answer['answer'])
        else:
            collection.delete_one({"_id":cached_answer["_id"]})
    
    context=[*initial_context]

    if format=="json": 
        context.append(system_message(f"Respond using json format. Example:`{example_response}`. The system will read the contents of {answer_key}."))

    context.append( user_message(question) )

    while True:
        try:
            data=await async_complete(
                context=context,
                provider=provider,
                format=format,
                streaming=streaming,
                streaming_callback=stream_handler
            )
            result=extractor(data[answer_key] if format=="json" else data)
            if result:
                print("ANSWERED",datetime.datetime.now())
                print(data)
                collection.insert_one({
                    "question":question,
                    "answer":data,
                    "format":format,
                    "expires_at":datetime.datetime.now()+datetime.timedelta(seconds=expires_in)
                })
                return result
            else:
                raise Exception("No result")

        except Exception as e:
            print("somthing bad happened in ask!")
            print(traceback.format_exc())
            context += [
                system_message("An error occured. Please try again."),
                system_message("Error: "+traceback.format_exc()),    
                system_message(f"Respond using json format. Example:`{example_response}`. The system will read the contents of {answer_key}." if format=="json" else "Respond using plain text."),
            ]
            await asyncio.sleep(1)
            continue
