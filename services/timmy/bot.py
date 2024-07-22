import asyncio
import datetime
import json
import random
from shared.data import assistant_message, system_message, user_message
from completion import async_complete

from context import get_context     
from shared.mongodb import timmy_answer_cache_collection, discord_message_collection



class Bot:
    def __init__(self,client, 
                 answer_cache_collection=timmy_answer_cache_collection,
                 message_collection=discord_message_collection):
        self.answer_cache_collection=answer_cache_collection
        self.message_collection=message_collection
        self.client=client
        self.state={}

    async def question_answer_tuple(self,question,context,extractor,format,force,expires_in=random.randint(12000,60000)):
        answer=await self.ask(question,context,extractor,expires_in=expires_in,format=format,force=force)
        return [user_message(question),assistant_message(answer)]
    def ask_docs(self,question, docs, expires_in=random.randint(12000,60000), force=False, extractor=lambda x: x, format="json"):
        return self.ask_context(
            question,
            initial_context=get_context(docs,self.client),
            expires_in=expires_in,
            force=force,
            extractor=extractor,
            format=format
        )
    def ask_doc_qa(self,question, docs, expires_in=random.randint(12000,60000), force=False, extractor=lambda x: x,format="json"):
        return self.question_answer_tuple(
            question,
            context=get_context(docs,self.client),
            expires_in=expires_in,
            extractor=extractor,
            force=force,
            format=format
        )

    async def query(
        self,
        question,
        initial_context,
        extractor=lambda x: x, # Extracts the object we want from the data we get back.
        format="json", # The format of the response.
        expires_in=60000,
        force=False,
        collection=timmy_answer_cache_collection,
        # Only used if format is json.
        answer_key="answer", # The key to extract the answer from the response.
        example_response={"answer":"This is an example response."}, # An example response to help the model.
        ):

        cached_answer=collection.find_one({"question":question})
        print("ASKING",question,cached_answer,datetime.datetime.now())

        if cached_answer and not force:
            if  cached_answer["expires_at"]>datetime.datetime.now():
                print("CACHE HIT",question,cached_answer["answer"])
                return extractor(cached_answer["answer"])
            else:
                print("CACHE EXPIRED",question,cached_answer["answer"],cached_answer["expires_at"])
                collection.delete_one({"_id":cached_answer["_id"]})
        
        context=initial_context+[
            system_message("Answer the users question given the context."),
            system_message("Respond using json format." if format=="json" else "Respond using plain text."),
            user_message(question)
        ]
        answer=await async_complete(
            context,
            state=self.state,
            example_response=example_response,
            answer_key=answer_key,
            format=format
        )
        collection.insert_one({
            "question":question,
            "answer":answer,
            "expires_at":datetime.datetime.now()+datetime.timedelta(milliseconds=expires_in)
        })
        return extractor(answer)