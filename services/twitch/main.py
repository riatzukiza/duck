import os
from twitchio.ext import commands
import discord

intents = discord.Intents.default()
client = discord.Client(intents=intents)

DISCORD_TWITCH_CHANNEL_ID=os.environ['DISCORD_TWITCH_CHANNEL_ID']
# Set your Twitch credentials here
TWITCH_TOKEN = os.environ['TWITCH_TOKEN']  # Your OAuth token
TWITCH_CLIENT_ID = os.environ['TWITCH_CLIENT_ID']  # Your Client ID
TWITCH_NICK = os.environ['TWITCH_NICK']  # Your Twitch username
TWITCH_PREFIX = '!'
TWITCH_INITIAL_CHANNELS = ['miss_taken_id']  # List of channels to join

class Bot(commands.Bot):

    def __init__(self):
        super().__init__(token=TWITCH_TOKEN, client_id=TWITCH_CLIENT_ID, nick=TWITCH_NICK, prefix=TWITCH_PREFIX, initial_channels=TWITCH_INITIAL_CHANNELS)

    async def event_ready(self):
        print(f'Logged in as | {self.nick}')
        print(f'User id is | {self.user_id}')

    async def event_message(self, message):
        print(f'{message.author.name}: {message.content}')
        await self.handle_commands(message)

    @commands.command(name='hello')
    async def hello(self, ctx):
        await ctx.send(f'Hello {ctx.author.name}!')

if __name__ == '__main__':
    bot = Bot()
    bot.run()
