To create a Python script that sends chunks of Wikipedia articles to a Discord channel with random intervals between 1 and 10 seconds, you'll need to use the `discord.py` library for interacting with Discord and the `wikipedia-api` library for fetching Wikipedia articles. 

First, make sure you have the necessary libraries installed:

```bash
pip install discord.py wikipedia-api
```

Here is the script:

```python
import discord
import wikipediaapi
import asyncio
import random

# Set up the Wikipedia API
wiki_wiki = wikipediaapi.Wikipedia('en')

# Discord bot token and channel ID
TOKEN = 'YOUR_DISCORD_BOT_TOKEN'
CHANNEL_ID = YOUR_CHANNEL_ID

# Define a client for discord
intents = discord.Intents.default()
client = discord.Client(intents=intents)

# Function to fetch and chunk Wikipedia content
def get_wikipedia_chunks(page_title, chunk_size=200):
    page = wiki_wiki.page(page_title)
    if not page.exists():
        return ["Page not found."]
    content = page.text
    return [content[i:i+chunk_size] for i in range(0, len(content), chunk_size)]

# Event listener when the bot has connected to the server
@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    channel = client.get_channel(CHANNEL_ID)
    
    # Change the title to the Wikipedia article you want to fetch
    page_title = 'Python (programming language)'
    chunks = get_wikipedia_chunks(page_title)
    
    for chunk in chunks:
        await channel.send(chunk)
        await asyncio.sleep(random.randint(1, 10))

# Run the bot
client.run(TOKEN)
```

### Explanation:
1. **Imports and Setup**:
    - `discord`: For interacting with the Discord API.
    - `wikipediaapi`: For fetching Wikipedia articles.
    - `asyncio` and `random`: For handling asynchronous delays and random intervals.

2. **Wikipedia API Initialization**: Sets up the Wikipedia API client to fetch articles in English.

3. **Discord Bot Initialization**:
    - `TOKEN`: Replace `'YOUR_DISCORD_BOT_TOKEN'` with your actual Discord bot token.
    - `CHANNEL_ID`: Replace `YOUR_CHANNEL_ID` with the actual ID of the channel where you want to send messages.

4. **Fetching and Chunking Wikipedia Content**:
    - `get_wikipedia_chunks`: Fetches the Wikipedia page content and splits it into chunks of 200 characters each.

5. **Event Listener `on_ready`**:
    - Sends each chunk to the specified Discord channel with a random delay between 1 and 10 seconds.

Make sure your bot has permission to send messages to the specified channel. To get your bot's token and channel ID, you need to create a bot on the Discord Developer Portal and invite it to your server with appropriate permissions.