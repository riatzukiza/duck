# -*- coding: utf-8 -*-
import discord
import requests
from discord.ext import commands, voice_recv, tasks
import collections
from dotenv import load_dotenv
import os
import discord
from ollama import AsyncClient

import aiohttp
import asyncio



ollama_client = AsyncClient("http://localhost:11434")
discord.opus._load_default()

bot = commands.Bot(command_prefix=commands.when_mentioned, intents=discord.Intents.all())
system_prompt = {"role": "system",
                 "content": """
                 You are a friendly, but sassy robot named Duck on discord that responds to transcribed voice.
                 Sometimes the transcripts will be a little wrong, but you know how to figure out what they meant.
                 There are a lot of people talking, so you need to be quick and concise in your responses.
                 The transcripts you'll recieve will be from a voice channel, so it might not be perfect.
                 There will be several people talking at once, so you need to be able to handle that.
                 You're responding to the group, not an individual.
                 The transcripts you'll recieve will be in the format:
                    {member1.name} said: {transcript}
                    {member2.name} said: {transcript}
                    {member1.name} said: {transcript}
                    {member3.name} said: {transcript}
                 you'll either respond when everyone has been quite for a few seconds, or when you've recieved a signifigant number of transcripts.
                 signifigance is weighted by how long the transcript is, and how many people are talking.
                 """},

import io
import wave

def wrap_pcm_in_wav(pcm_data: bytes, sample_rate=48000, channels=2, sample_width=2) -> io.BytesIO:
    wav_io = io.BytesIO()
    with wave.open(wav_io, 'wb') as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_data)
    wav_io.seek(0)
    return wav_io

async def transcribe_pcm(pcm_data, url='http://localhost:5000/transcribe_pcm'):
    headers = {
        'Content-Type': 'application/octet-stream',
        'X-Sample-Rate': "48000",
        'X-Dtype': 'int16'
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=pcm_data, headers=headers) as response:
            if response.status == 200:
                json_data = await response.json()
                print("Transcription:", json_data.get('transcription'))
                return json_data.get('transcription')
            else:
                text = await response.text()
                print("Error:", response.status, text)
                return None

async def generate_voice(text, url='http://localhost:5000/synth_voice'):
    data = {
        "input_text": text
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=data) as response:
            if response.status == 200:
                return await response.read()  # Return audio bytes
            else:
                print("Error:", response.status, await response.text())
                return None

async def generate_response(transcript):
    response = await ollama_client.chat(model="llama3.2:1b", messages=[
        system_prompt,
        {"role": "user", "content": transcript}])
    response_text = response['message']['content']
    return generate_voice(response_text)

class DuckAgent:
    def __init__(self, user):
        self.user = user
        self.voice_client = None
        self.speaking = False
        self.last_speaking_time = None
        self.audio_bytes = b''
    def add_audio(self, audio_data):
        self.audio_bytes += audio_data
        self.last_speaking_time = discord.utils.utcnow()
    @property
    def is_speaking(self):
        return self.speaking
class Speaker:
    def __init__(self, user, call_transcript):
        self.user = user
        self.call_transcript = call_transcript
        self.audio_bytes = b''
        self.voice_client = None
        self.last_speaking_time = None
    def start_speaking(self):
        self.speaking = True
        self.last_speaking_time = discord.utils.utcnow()

    def stop_speaking(self):
        self.speaking = False
        self.last_speaking_time = None
    @property
    def waiting_for_transcription(self):
        return self.audio_bytes != b''

    async def transcribe_audio(self):
        transcription = await transcribe_pcm(self.audio_bytes)
        self.call_transcript.transcript += f"{self.user.name} said: {transcription}\n"
        self.audio_bytes = b''

    def add_audio(self, audio_data):
        self.audio_bytes += audio_data
        self.last_speaking_time = discord.utils.utcnow()
    @property
    def is_speaking(self):
        return self.speaking
class CallTranscript:
    def __init__(self):
        self.time_silent = 0
        self.transcript = ""
        self.speakers = {}

    @property
    def any_speaking(self):
        return any(speaker.is_speaking for speaker in self.speakers.values())
    def add_speaker(self, user):
        if user not in self.speakers:
            self.speakers[user] = Speaker(user, self.transcript)

    def add_audio(self, user, audio_data):
        if user in self.speakers:
            self.speakers[user].add_audio(audio_data)
        else:
            print(f"Speaker {user} not found in transcript")

    def clear(self):
        self.transcript = ""
        self.speakers.clear()

transcript= CallTranscript()
class MySink(voice_recv.AudioSink):
    def __init__(self):
        super().__init__()
    def wants_opus(self):
        return False
    def write(self, user, data):
        print(f"Got packet from {user}")
        # voice power level, how loud the user is speaking
        ext_data = data.packet.extension_data.get(voice_recv.ExtensionID.audio_power)
        value = int.from_bytes(ext_data, 'big')
        power = 127-(value & 127)
        print('#' * int(power * (79/128)))
        # instead of 79 you can use shutil.get_terminal_size().columns-1
        if user not in transcript.speakers:
            transcript.add_speaker(user)
        transcript.add_audio(user, data.pcm)

    @voice_recv.AudioSink.listener
    def on_voice_member_speaking_start(self, member):
        print(f"{member.name} started speaking")
        transcript.speakers[member.name].start_speaking()

    @voice_recv.AudioSink.listener
    def on_voice_member_speaking_stop(self, member):
        print(f"{member.name} stopped speaking")
        transcript.speakers[member.name].stop_speaking()

    def cleanup(self):
        print("Cleaning up streams")
        transcript.clear()



class Testing(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.vc = None

    @commands.command()
    async def test(self, ctx):
        self.vc = await ctx.author.voice.channel.connect(cls=voice_recv.VoiceRecvClient)
        sink = MySink()
        self.vc.listen(sink)
        self.response_loop.start()

    @tasks.loop(seconds=1)
    async def response_loop(self):
        if not self.vc or not self.vc.is_connected():
            self.handle_response_loop.stop()
            return
        for speaker in transcript.speakers:
            if not speaker.is_speaking and speaker.waiting_for_transcription:
                await speaker.transcribe_audio()
        if transcript.time_silent > 5 or len(transcript.transcript) > 1000:
            if transcript.transcript:
                print("Final Transcript:", transcript.transcript)
                response_audio = await generate_response(transcript.transcript)
                if response_audio:
                    self.vc.play(discord.FFmpegPCMAudio(response_audio), after=lambda e: print(f'Finished playing: {e}'))
            transcript.time_silent = 0
        else:
            transcript.time_silent += 1



    @commands.command()
    async def stop(self, ctx):
        await ctx.voice_client.disconnect()

    @commands.command()
    async def die(self, ctx):
        ctx.voice_client.stop()
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
