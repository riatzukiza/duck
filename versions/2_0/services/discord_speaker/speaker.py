import discord
from audio_block import AudioBlock
import asyncio

class Speaker:
    def __init__(self, user, call_transcript):
        self.user = user
        self.call_transcript = call_transcript
        self.audio_blocks = []
        self.pending_audio = []
        self.voice_client = None
        self.speaking = False
        self.current_audio_block = None

    def start_speaking(self):
        if self.speaking or self.current_audio_block is not None:
            print(f"Warning: {self.user.name} is already speaking.")
            return
        if not self.speaking and self.current_audio_block is not None:
            print(f"Warning: {self.user.name} started speaking without stopping the previous audio block.")
            self.current_audio_block.end()
            self.current_audio_block = None

        self.speaking = True
        self.current_audio_block = AudioBlock(self)

    def stop_speaking(self):
        if self.current_audio_block is None:
            print(f"Warning: {self.user.name} stopped speaking without a current audio block.")
            return
        if not self.speaking:
            print(f"Warning: {self.user.name} is not currently speaking.")
            return

        self.speaking = False
        self.current_audio_block.end()
        self.current_audio_block = None

    async def transcribe_audio(self):
        print("Transcribing audio for user:", self.user.name)
        processing_audio = []
        while self.pending_audio:
            block = self.pending_audio.pop()
            processing_audio.append(block.transcribe())
        await asyncio.gather(*processing_audio)

    def add_audio(self, audio_data):
        if self.current_audio_block is None:
            raise ValueError("No current audio block to add audio to.")
        self.current_audio_block.add_audio(audio_data)
    @property
    def is_speaking(self):
        return self.speaking
