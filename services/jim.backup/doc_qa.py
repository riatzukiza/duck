
import asyncio
import datetime
import json
import random
from shared.data import assistant_message, system_message, user_message
from completion import async_complete

import traceback

from context import get_context     
from shared.mongodb import timmy_answer_cache_collection

async def question_answer_tuple(
    question,
    context,
    extractor,
    format,
    force,
    state={},
    example_response={"result":"This is an example response."},
    answer_key="result",
    expires_in=random.randint(12000,60000)):
    answer=await ask_context(
        question,
        context,
        extractor,
        state=state,
        example_response=example_response,
        answer_key=answer_key,
        expires_in=expires_in,
        format=format,
        force=force)
    return [user_message(question),assistant_message(answer)]

def ask_docs(
    question, 
    docs,
    expires_in=random.randint(120,60000), 
    force=False, 
    extractor=lambda x: x, 
    state={},
    example_response={"result":"This is an example response."},
    answer_key="result",
    format=None,
    ):
    return ask_context(
        question,
        initial_context=get_context(docs),
        expires_in=expires_in,
        state=state,
        example_response=example_response,
        answer_key=answer_key,
        force=force,
        extractor=extractor,
        format=format
    )
def ask_doc_qa(
    question, 
    docs,
    state={},
    example_response={"result":"This is an example response."},
    answer_key="result",
    expires_in=random.randint(12000,60000), 
    force=False, 
    extractor=lambda x: x,
    format=None
    ):
    return question_answer_tuple(
        question,
        state=state,
        example_response=example_response,
        answer_key=answer_key,
        context=get_context(docs),
        expires_in=expires_in,
        extractor=extractor,
        force=force,
        format=format
    )

async def ask_context(
    question,
    initial_context,
    state={},
    example_response={"result":"This is an example response."},
    answer_key="result",
    extractor=lambda x: x, # Extracts the object we want from the data we get back.
    force=False,
    collection=timmy_answer_cache_collection,
    expires_in=60000,
    format=None
    ):

    cached_answer=collection.find_one({"question":question,"format":format})
    print("question",datetime.datetime.now())
    print(question)
    # print(f"state: {state}")

    if cached_answer and not force:
        if  cached_answer["expires_at"]>datetime.datetime.now():
            print("cached",datetime.datetime.now())
            print(cached_answer['answer'])
            return extractor(cached_answer['answer'][answer_key] if format=="json" else cached_answer['answer'])
        else:
            collection.delete_one({"_id":cached_answer["_id"]})
    
    context=initial_context+[
        system_message("Respond to the users query given the chat history and a state object."),
        system_message(f"Respond using json format. Example:`{example_response}`. The system will read the contents of {answer_key}." if format=="json" else "Respond using plain text."),
        system_message(f"The current state of the system is:`{state}`."),
        user_message(question),
    ]
    while True:
        try:
            data=await async_complete(
                context=context,
                format=format,
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
