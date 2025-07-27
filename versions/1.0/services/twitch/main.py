import os
import requests
from twitchio.ext import commands
import discord
import asyncio

# Initialize Discord intents and client
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
discord_client = discord.Client(intents=intents)

# Environment variables for Discord and Twitch
DISCORD_TWITCH_CHANNEL_ID = os.getenv('DISCORD_TWITCH_CHANNEL_ID')

TWITCH_CLIENT_ID = os.getenv('TWITCH_CLIENT_ID')
TWITCH_SECRET = os.getenv('TWITCH_SECRET')

TWITCH_NICK = os.getenv('TWITCH_NICK')
TWITCH_PREFIX = '!'
TWITCH_INITIAL_CHANNELS = [os.getenv('TWITCH_NICK')]  # List of channels to join

# Initialize readiness flags
discord_ready = False
twitch_ready = False

# This function retrieves the OAuth token
def get_token(client_id=TWITCH_CLIENT_ID, client_secret=TWITCH_SECRET):
    auth_url = 'https://id.twitch.tv/oauth2/token'
    auth_params = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'client_credentials'
    }
    response = requests.post(auth_url, params=auth_params)
    auth_response = response.json()
    print("OAuth Token Response:", auth_response)  # Debug information
    if 'access_token' not in auth_response:
        raise Exception("Failed to retrieve access token")
    return auth_response['access_token']

# Define your Twitch bot class
class Bot(commands.Bot):

    def __init__(self, token):
        super().__init__(token=token, client_id=TWITCH_CLIENT_ID, nick=TWITCH_NICK, prefix=TWITCH_PREFIX, initial_channels=TWITCH_INITIAL_CHANNELS)

    async def event_ready(self):
        global twitch_ready
        print(f'Logged in as | {self.nick}')
        print(f'User id is | {self.user_id}')
        twitch_ready = True

    async def event_message(self, message):
        if message.echo:
            return
        print(f'{message.author.name}: {message.content}')

        if discord_ready:
            discord_channel = discord_client.get_channel(int(DISCORD_TWITCH_CHANNEL_ID))
            await discord_channel.send(f'{message.author.name}: {message.content}')

        await self.handle_commands(message)

    @commands.command(name='hello')
    async def hello(self, ctx):
        await ctx.send(f'Hello {ctx.author.name}!')

# Create a global instance of the Twitch bot
twitch_bot = None

# Discord bot event
@discord_client.event
async def on_ready():
    global discord_ready
    discord_ready = True
    print(f'Logged in as {discord_client.user}')

@discord_client.event
async def on_message(message):
    # Ignore messages from the bot itself
    if message.author == discord_client.user:
        return

    # Only forward messages from the specific channel
    if str(message.channel.id) == DISCORD_TWITCH_CHANNEL_ID:
        if twitch_ready:
            channel = twitch_bot.get_channel(TWITCH_NICK)
            if channel:
                print("sending message to twitch",message)
                print(f"{message.author.name}: {message.content}")
                await channel.send(f'{message.author.name}: {message.content}')

# Run the Twitch and Discord bots concurrently
async def main():
    global twitch_bot

    CLIENT_ID = os.getenv('TWITCH_CLIENT_ID')
    CLIENT_SECRET= os.getenv('TWITCH_SECRET')
    AUTH_CODE=os.getenv('TWITCH_AUTH_CODE')

    REDIRECT_URI = 'http://localhost'


    token_url = 'https://id.twitch.tv/oauth2/token'

    token_params = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'code': AUTH_CODE,
        'grant_type': 'authorization_code',
        'redirect_uri': REDIRECT_URI,
    }

    response = requests.post(token_url, params=token_params)
    token_data = response.json()
    print("Access Token Response:", token_data)
    twitch_bot = Bot(token=token_data['access_token'])
    await asyncio.gather(
        twitch_bot.start(),
        discord_client.start(os.getenv('DISCORD_TOKEN'))
    )

if __name__ == "__main__":
    asyncio.run(main())
