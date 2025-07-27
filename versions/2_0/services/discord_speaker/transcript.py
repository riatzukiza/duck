from speaker import Speaker
from bot_response import BotResponse

class CallTranscript:
    def __init__(self):
        self.time_silent = 0
        self.speakers = {}
        self.waiting_audio = []
        self.bot_responses = []


    @property
    def history(self):
        history=sorted([*self.bot_responses, *self.transcribed_audio_blocks],key=lambda block: block.start)
        return history

    @property
    def transcribed_audio_blocks(self):
        return [ block for speaker in self.speakers.values() for block in speaker.audio_blocks if block.is_transcribed]
    @property
    def text(self):
        return "\n".join(block.text for block in self.transcribed_audio_blocks )

    @property
    def any_speaking(self):
        return any(speaker.is_speaking for speaker in self.speakers.values())

    def add_speaker(self, user):
        if user.name not in self.speakers:
            self.speakers[user.name] = Speaker(user, self)

    def add_bot_response(self, text):
        self.bot_responses.append(BotResponse(text))

    def add_audio(self, user, audio_data):
        if user.name in self.speakers:
            if not self.speakers[user.name].is_speaking:
                self.speakers[user.name].start_speaking()
            self.speakers[user.name].add_audio(audio_data)
        else:
            print(f"Speaker {user} not found in transcript")

    def clear(self):
        self.speakers.clear()
