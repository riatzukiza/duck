
"""Tools for managing the state that persists between contexts.
"""
import asyncio
from io import BytesIO
import json
import random
import os

def get_file_extension(file_path):
    _, file_extension = os.path.splitext(file_path)
    return file_extension


from sent_messages import sent_messages
from shared.discord import get_latest_channel_docs, send_message, split_markdown
from shared.doc_qa import ask_docs
from shared.persistant_set import PersistentSet
from shared.mongodb import discord_message_collection,db

from discord_client import client
completed_searches=PersistentSet("completed_searches.pkl")
scraped_sources=PersistentSet("scraped_sources.pkl")

state = json.load(open("state.json",'r'))

import chromadb
chroma_client = chromadb.PersistentClient(path="./chroma_db")

# Function to get embeddings from Ollama
def get_embedding(text):
    response = client.get_embedding(text)
    return response['embedding']

# Initialize ChromaDB
search_chroma = chroma_client.get_or_create_collection(name="search_results")
discord_chroma = chroma_client.get_or_create_collection(name="discord_messages")

def get_documents_by_ids(ids):
    # Connect to MongoDB

    # Convert string IDs to ObjectId

    # Query to find documents with the specified IDs
    documents = discord_message_collection.find({'_id': {'$in': ids}})

    # Convert the cursor to a list
    document_list = list(documents)
    
    return document_list

def update_state(new_state):
    state.update(new_state)
    json.dump(state,open("state.json",'w'))
    return state

def format_search_result(key,result,chunk,page_num):
    return f"""
[{result['title']}]({result['href']})
{chunk}
        """

import requests
import html2text

def fetch_webpage(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.text

def convert_html_to_markdown(html_content):
    converter = html2text.HTML2Text()
    converter.ignore_links = False
    return split_markdown(converter.handle(html_content))

def split_into_chunks(input_string, chunk_size=1000):
    '''Splits the input string into chunks of specified size.'''  
    return [input_string[i:i + chunk_size] for i in range(0, len(input_string), chunk_size)]

import PyPDF2

import requests
from io import BytesIO
from PyPDF2 import PdfReader

async def process_pdf(pdf_source: str, is_local_file: bool):
    # Process the PDF from URL or local file
    if not is_local_file:
        response = requests.get(pdf_source)
        file = BytesIO(response.content)
    else:
        file = open(pdf_source, 'rb')

    # Extract text from PDF
    pdf_reader = PdfReader(file)
    text = ""
    for page in range(pdf_reader.numPages):
        text += pdf_reader.getPage(page).extractText()

    if not is_local_file:
        file.close()
    return text



async def generate_state_property_update( question,key,example,get_docs=get_latest_channel_docs):

    discord_similar_docs = get_documents_by_ids(discord_chroma.query(query_texts=[question], n_results=10)['ids'][0])
    search_results= search_chroma.query(query_texts=[question], n_results=10)['documents'][0]
    value=await ask_docs(
        f"Update {key} with response to '{question}'.",
        state=state,
        # provider="http://192.168.0.16:11434",
        example_response={key:example},
        answer_key=key,
        docs=get_docs()+discord_similar_docs,
        format="json",
        search_results=search_results,
        expires_in=random.randint(1,60)*60,
    )
    update_state({key:value})
    return value

async def update_state_from_search( question,key,examples=["Search term","AI","hacking","bananas","minecraft recipes"],get_docs=get_latest_channel_docs):
    from duckduckgo_search import AsyncDDGS

    # Define the search keywords
    keywords = await generate_state_property_update(
        f"Generate a list of search terms from '{question}'",
        f'{key}_search_keywords',
        examples,
        get_docs
    )
    print("duck duck go search keywords",keywords)

    # Perform the search
    for keyword in keywords:
        try:
            print("searching for",keyword)

            if keyword in completed_searches:
                continue
            for result in (await AsyncDDGS().atext(keyword, region='wt-wt', safesearch='Moderate', max_results=10)):
                    await asyncio.sleep(1)
                    if result['href'] in scraped_sources:
                        print("cached source",result['href'])
                        continue
                    if "pdf" in result['href']:
                        print("pdf source",result['href'])
                        try:
                            markdown=[await process_pdf(result['href'])]
                        except Exception as e:
                            print("error processing pdf",e)
                            continue
                    else:
                        print("html source",result['href'])
                        await asyncio.sleep(1)
                        markdown=convert_html_to_markdown(fetch_webpage(result['href']))

                    completed_searches.add(keyword)
                    scraped_sources.add(result['href'])

                    await asyncio.sleep(1)
                    for text in markdown:
                        for i,chunk in enumerate(split_into_chunks(text,chunk_size=1000)):
                            text=format_search_result(keyword,result,chunk,i) 
                            print(text)
                            search_chroma.upsert(ids=[f"{result['href']}-{i}"], documents=[text],metadatas=[{"title":result['title'],"url":result['href'], "keyword":keyword}])
        except Exception as e:
            print("error getting search results",e)