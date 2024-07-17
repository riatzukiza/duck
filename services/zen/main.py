
import discord
from shared.discord import all_commands

import shared.settings as settings
# Set up the Wikipedia API

# Discord bot token and channel ID
CHANNEL_ID = settings.DEFAULT_CHANNEL

# Define a client for discord
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)


# Command to clear the unsent messages and start over
@client.event
async def on_message(message):
    await all_commands(message,client)

# Run the bot
client.run(settings.DISCORD_TOKEN)
