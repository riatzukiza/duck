# -*- coding: utf-8 -*-
from voice import wrap_pcm_in_wav
from llm import attempt_to_respond
import io
import discord
# print("discord.py version:", discord.__version__)
from discord.ext import commands, voice_recv, tasks
print(discord.__file__)

from discord.opus import Decoder as OpusDecoder
from dotenv import load_dotenv
import os
import discord
from transcript import CallTranscript
from sink import MySink

import aiohttp
import asyncio


CHANNELS = OpusDecoder.CHANNELS
SAMPLE_WIDTH = OpusDecoder.SAMPLE_SIZE // OpusDecoder.CHANNELS
SAMPLING_RATE = OpusDecoder.SAMPLING_RATE
discord.opus._load_default()

bot = commands.Bot(command_prefix=commands.when_mentioned, intents=discord.Intents.all())



async def post(url,data):
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=data) as response:
            if response.status == 200:
                return await response.read()  # Return audio bytes
            else:
                print("Error:", response.status, await response.text())
                return None

async def attempt_vc_connection(ctx, cog):
    cog.vc = None
    while not cog.vc:
        try:
            cog.vc = await ctx.author.voice.channel.connect(cls=voice_recv.VoiceRecvClient)
            await asyncio.sleep(1)  # Wait a bit before trying to listen again
            await ctx.send(f"Connected to voice channel: {ctx.author.voice.channel.name}")

        except discord.ClientException as e:
            if not f"{e}" == "Already connected to a voice channel.":
                await ctx.send(f"Error connecting to voice channel: {e}")
                cog.vc = None
async def attempt_vc_listen(ctx,cog):
    is_listening = False
    await attempt_vc_connection(ctx, cog)
    while not is_listening:
        try:
            await asyncio.sleep(1)  # Wait a bit before trying to listen again
            await ctx.send("Listening for audio...")
            await asyncio.sleep(1)  # Wait a bit before trying to listen again

            cog.vc.listen(MySink(cog.transcript))
            is_listening = True

            await asyncio.sleep(1)  # Wait a bit before trying to listen again
        except discord.ClientException as e:
            await ctx.send(f"Error starting audio sink: {e}")
            is_listening = False

          
class Testing(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.vc = None
        self.transcript= CallTranscript()

    @commands.command()
    async def ping(self, ctx):
        """Responds with Pong!"""
        return await ctx.send('Pong!')

    @commands.command()
    async def test(self, ctx):
        await ctx.send("Starting transcription test...")
        await asyncio.sleep(1)  # to stagger the loops so they aren't happening at the same times.

        await attempt_vc_listen(ctx, self)



        await asyncio.sleep(5)  # to stagger the loops so they aren't happening at the same times.
        await ctx.send("Starting transcription and response loops...")
        await asyncio.sleep(6)  # ""
        self.transcription_loop.start()

        await asyncio.sleep(7)  # ""
        self.response_loop.start()


    @tasks.loop(seconds=5)
    async def transcription_loop(self):
        pending_transcriptions=[]
        print("gathering audio for transcription...")
        for name, speaker in self.transcript.speakers.items():
            pending_transcriptions.append(
                speaker.transcribe_audio()
            )

        await asyncio.gather(*pending_transcriptions)
    @tasks.loop(seconds=10)
    async def response_loop(self):
        print("Running response loop...")
        if (self.transcript.time_silent > 5
            and self.transcript.text != ""):
            if self.transcript.text:
                print("Final Transcript:", self.transcript.text)
                response_audio = await attempt_to_respond(self.transcript)
                if response_audio:
                    self.transcript.waiting_audio.append(response_audio)

            self.transcript.time_silent = 0
        else:
            self.transcript.time_silent += 1
            print(f"Transcript is not ready yet, waiting... Time silent: {self.transcript.time_silent}")

    @tasks.loop(seconds=1)
    async def voice_loop(self):
        if len(self.transcript.waiting_audio) > 0 and not self.vc.is_playing():
            self.vc.play(discord.PCMAudio(wrap_pcm_in_wav(self.transcript.waiting_audio.pop())),
                         after=lambda e: print(f'Finished playing: {e}'))


    @commands.command()
    async def stop(self, ctx):
        await ctx.voice_client.disconnect(force=True)
        self.response_loop.stop()
        self.transcription_loop.start()

    @commands.command()
    async def die(self, ctx):
        ctx.voice_client.stop()
        self.response_loop.stop()
        self.transcription_loop.stop()
        await ctx.bot.close()

@bot.event
async def on_ready():
    print('Logged in as {0.id}/{0}'.format(bot.user))
    print('------')

@bot.event
async def setup_hook():
    await bot.add_cog(Testing(bot))

load_dotenv()
bot.run(os.getenv('DISCORD_TOKEN', 'your_token_here'))
