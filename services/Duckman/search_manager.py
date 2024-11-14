import asyncio
import json
import random
from duckduckgo_search import AsyncDDGS

from shared.discord import get_latest_channel_docs
from shared.embeddings import generate_embedding
from shared.mongodb import db

from shared import settings

from shared.discord_text_splitter import split_markdown
from shared.persistant_set import PersistentSet
from state import generate_state_property_update,state
import requests
import html2text

import chromadb
from shared.mongodb import discord_message_collection

import requests
from io import BytesIO
from PyPDF2 import PdfReader

chroma_client = chromadb.PersistentClient(path="./chroma_db")


completed_searches=PersistentSet("completed_searches.pkl")
scraped_sources=PersistentSet("scraped_sources.pkl")

# Initialize ChromaDB
search_chroma = chroma_client.get_or_create_collection(name="search_results")
discord_chroma = chroma_client.get_or_create_collection(name="discord_messages")
search_mongo = db["search_results"]



def format_search_result(key,result,chunk,page_num):
    return f"""
[{result['title']}]({result['href']})
{chunk}
        """
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
async def handle_search_result(result,keyword):
    await asyncio.sleep(1)
    if result['href'] in scraped_sources:
        print("cached source",result['href'])
    elif "pdf" in result['href']:
        print("pdf source",result['href'])
        try:
            return [await process_pdf(result['href'])]
        except Exception as e:
            print("error processing pdf",e)
    else:
        print("html source",result['href'])
        await asyncio.sleep(1)
        markdown=convert_html_to_markdown()

    completed_searches.add(keyword)
    scraped_sources.add(result['href'])

async def update_state_from_search( question,key,examples=["Search term","AI","hacking","bananas","minecraft recipes"],get_docs=get_latest_channel_docs):

    # Define the search keywords
    # We want to move away from this approach.
    # We don't use the state property the same way any more.
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
            for result in (await AsyncDDGS().atext(keyword, region='wt-wt', safesearch='Moderate', max_results=10)):
                handle_search_result(result,keyword)


        except Exception as e:
            print("error getting search results",e)
async def main():
    while True:
        messages=get_latest_channel_docs(state.get("channel_id",settings.DEFAULT_CHANNEL))
        choice=random.choice(messages)
        await update_state_from_search(
            choice['content'],
            "random_message"
        )
        await asyncio.sleep(60)

asyncio.run(main())
