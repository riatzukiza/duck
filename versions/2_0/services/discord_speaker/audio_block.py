from discord.opus import Decoder as OpusDecoder
from lib.date_tools import time_ago
import discord
import wave
import aiohttp
import io
import time
import uuid
import json
from ollama import AsyncClient

CHANNELS = OpusDecoder.CHANNELS
SAMPLE_WIDTH = OpusDecoder.SAMPLE_SIZE // OpusDecoder.CHANNELS
SAMPLING_RATE = OpusDecoder.SAMPLING_RATE

ollama_client = AsyncClient("http://localhost:11434")


async def cleanup_transcript(raw_transcript, speakers=None, audio_blocks=None, voice_client=None):
    """
    Cleans up the transcript by clearing speakers and audio blocks.
    Optionally closes the voice client if provided.
    """
    response = await ollama_client.chat(
        model="llama3.2",
        format={
            "type":"object",
            "properties": {
                "transcript": {
                    "type": "string",
                    "description": "The cleaned up version of the transcript."
                }
            }
        },
        messages=[
            {"role": "system",
             "content": """Respond with JSON. You are a transcript cleaner. Your job is to take raw, messy transcripts generated from real-time speech-to-text and rewrite them into clear, coherent English. The original may contain filler words, stuttering, false starts, missing punctuation, poor spacing, or transcription errors. Your task is to:

Fix spelling and grammar issues.

Insert punctuation and sentence boundaries where appropriate.

Preserve the original speaker’s intent and tone.

Remove filler words, false starts, and repeated phrases unless they add meaning.

Do not add new information or make assumptions beyond what’s implied.

If a sentence is too garbled to understand, simplify it without guessing. It's okay to mark uncertain sections with brackets like: [unclear]"""},
            {"role": "user", "content": raw_transcript}])
    print("respons", response['message']['content'])
    return json.loads(
        response['message']['content']
    ).get(
        'transcript',
        raw_transcript
    )

async def transcribe_pcm(pcm_data, url='http://localhost:5001/transcribe_pcm/equalized'):
    headers = {
        'Content-Type': 'application/octet-stream',
        'X-Dtype': 'int16',
        'X-Sample-Rate': str(SAMPLING_RATE),
    }
    print("Sending PCM data for transcription...")

    pcm_data.seek(0)

    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=pcm_data, headers=headers) as response:
        # async with session.post(url, data=pcm_data, headers=headers) as response:
            if response.status == 200:
                json_data = await response.json()
                print("Transcription:", json_data.get('transcription'))
                return json_data.get('transcription')
            else:
                text = await response.text()
                print("Error:", response.status, text)
                return None
class AudioBlock:
    def __init__(self, speaker):
        self._id = str(uuid.uuid4())
        self.speaker = speaker
        self.start = discord.utils.utcnow()
        self.is_transcribing = False
        self.stop = None
        self.transcribed_text = ""
        self.wav_io = io.BytesIO()
        self.wav=wave.open(self.wav_io, 'wb')
        self.wav.setnchannels(CHANNELS)
        self.wav.setsampwidth(SAMPLE_WIDTH)
        self.wav.setframerate(SAMPLING_RATE)

    @property
    def id(self): return self._id

    @property
    def timestamp(self):
        return time_ago(self.start)
    @property
    def user(self):
        return self.speaker.user
    @property
    def is_transcribed(self):
        return self.stop is not None and self.transcribed_text != ""
    @property
    def is_closed(self):
        return self.wav is None
    @property
    def is_open(self):
        return self.wav is not None
    @property
    def is_stopped(self):
        return self.stop is not None

    def end(self):
        self.stop = discord.utils.utcnow()
        self.speaker.pending_audio.append(self)

    @property
    def text(self):
        if self.is_transcribed:
            return f"{self.user.name}({self.timestamp}): {self.transcribed_text}"
        return None
    async def transcribe(self):

        print("transcribing audio for user:", self.user.name, self.id)
        print("AudioBlock ID:", self.id, "User:", self.user.name, "is_transcribing:", self.is_transcribing, "is_transcribed:", self.is_transcribed, "is_closed:", self.is_closed, "is_open:", self.is_open, "is_stopped:", self.is_stopped)
        print("AudioBlock start time:", self.start, "stop time:", self.stop, "is_transcribing:", self.is_transcribing, "is_transcribed:", self.is_transcribed )

        self.is_transcribing = True
        if self.wav_io is None or self.wav is None:
            print("AudioBlock is closed for writing, cannot transcribe.")
            return
        raw_transcribed_text = await transcribe_pcm(self.wav_io)
        if raw_transcribed_text is None:
            print(f"Transcription failed for {self.user.name}")
            self.transcribed_text = "Transcription failed"
        else:
            self.transcribed_text = await cleanup_transcript(raw_transcribed_text)
            print(f"Transcription result for {self.user.name}:", self.text)


        self.is_transcribing = False
        self.wav_io = None
        self.wav = None
        self.speaker.audio_blocks.append(self)

    def add_audio(self, audio_data):
        if self.wav is None:
            raise ValueError("AudioBlock is closed for writing")
        self.wav.writeframes(audio_data)
