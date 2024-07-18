
import asyncio
import datetime
import json
import random
from shared.data import assistant_message, system_message, user_message
from completion import async_complete

from context import get_context     
from shared.mongodb import timmy_answer_cache_collection


def ask_docs(question, docs,client, expires_in=random.randint(12000,60000), force=False, check=lambda x: x, format="json"):
    return ask_context(
        question,
        initial_context=get_context(docs,client),
        expires_in=expires_in,
        force=force,
        check=check,
        format=format
    )
def ask_doc_qa(question, docs,client, expires_in=random.randint(12000,60000), force=False, check=lambda x: x,format="json"):
    return question_answer_tuple(
        question,
        context=get_context(docs,client),
        expires_in=expires_in,
        check=check,
        force=force,
        format=format
    )

async def ask_context(
    question,
    initial_context,
    check=lambda x: x,
    force=False,
    collection=timmy_answer_cache_collection,
    expires_in=60000,
    format="json"
    ):

    matches_schema=False
    data=None
    cached_answer=collection.find_one({"question":question})
    print("ASKING",question,cached_answer,datetime.datetime.now())

    if cached_answer and not force:
        if  cached_answer["expires_at"]>datetime.datetime.now():
            print("CACHE HIT",question,cached_answer["answer"])
            return check(cached_answer["answer"])
        else:
            print("CACHE EXPIRED",question,cached_answer["answer"],cached_answer["expires_at"])
            collection.delete_one({"_id":cached_answer["_id"]})
    
    context=initial_context+[
        system_message("Answer the users question given the context."),
        system_message("Respond using json format." if format=="json" else "Respond using plain text."),
        user_message(question)
    ]
    while True:
        try:
            data=await async_complete(
                context=context,
                format=format,
            )
            result=check(data)


            if result:
                print("MATCHES SCHEMA",question,data)
                print("result",result)
                collection.insert_one({
                    "question":question,
                    "answer":data,
                    "format":format,
                    "expires_at":datetime.datetime.now()+datetime.timedelta(seconds=expires_in)
                })
                return result
            else:
                print("DOES NOT MATCH SCHEMA",question,data)
                continue

        except Exception as e:
            print("somthing bad happened in ask!",data)
            print(e)
            context += [
                system_message("An error occured. Please try again."),
                system_message("Error: "+str(e))    
            ]
            await asyncio.sleep(10)
            continue

async def question_answer_tuple(question,context,check,format,force,expires_in=random.randint(12000,60000)):
    answer=await ask_context(question,context,check,expires_in=expires_in,format=format,force=force)
    return [user_message(question),assistant_message(answer)]