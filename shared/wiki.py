import asyncio
import random
from shared import settings
import wikipediaapi

user_agent = 'Duckbot/1.0 (https://github.com/riatzukiza/discord-chatter)'
wiki_wiki = wikipediaapi.Wikipedia(user_agent)

# Function to fetch and chunk Wikipedia content
def get_wikipedia_chunks(page_title):
    page = wiki_wiki.page(page_title)
    if not page.exists():
        return ["Page not found."]

    # Split into line. filter out empty strings.
    # split the lints into sentances.
    # flatten to a list of strings
    return [sentance for line in page.text.split("\n") for sentance in line.split(".") if len(sentance)>0 ]

# Function to fetch links from a Wikipedia page
def get_page_links(page_title):
    page = wiki_wiki.page(page_title)
    if not page.exists():
        return []
    return list(page.links.keys())

async def crawl(title,message,client):
    # Fetch a random Wikipedia page
    channel=client.get_channel(int(message.channel.id or settings.DEFAULT_CHANNEL))
    await channel.send(f"Random article: {title}")
    
    # Get and send chunks of the random page
    chunks = get_wikipedia_chunks(title)
    for chunk in chunks:
        await channel.send(chunk)
        await asyncio.sleep(random.randint(5, 10))
    
    # Get links from the random page
    links = get_page_links(title)
    if links:
        await crawl(title=random.choice(links),message=message)
    else:
        await channel.send("No links found in the random article.")