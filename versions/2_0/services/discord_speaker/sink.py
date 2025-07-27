from discord.ext import voice_recv
from discord.opus import Decoder as OpusDecoder

CHANNELS = OpusDecoder.CHANNELS
SAMPLE_WIDTH = OpusDecoder.SAMPLE_SIZE // OpusDecoder.CHANNELS
SAMPLING_RATE = OpusDecoder.SAMPLING_RATE


print(f"Opus decoder initialized with {CHANNELS} channels, ")
print(f"sample width {SAMPLE_WIDTH} bytes, ")
print(f"and sampling rate {SAMPLING_RATE} Hz.")

class MySink(voice_recv.AudioSink):
    def __init__(self, transcript):
        super().__init__()
        self.transcript= transcript
       
    def wants_opus(self):
        return False
    def write(self, user, data):
        # print(f"Got packet from {user}")
        # voice power level, how loud the user is speaking
        # ext_data = data.packet.extension_data.get(voice_recv.ExtensionID.audio_power)
        # value = int.from_bytes(ext_data, 'big')
        # print("Got packet from", user.name, "with power level:", value)

        # power = 127-(value & 127)
        # print('#' * int(power * (79/128)))
        # instead of 79 you can use shutil.get_terminal_size().columns-1
        if user.name not in self.transcript.speakers:
            self.transcript.add_speaker(user)
        self.transcript.add_audio(user, data.pcm)

    @voice_recv.AudioSink.listener()
    def on_voice_member_speaking_start(self, member):
        print(f"{member.name} started speaking")
        if member.name not in self.transcript.speakers:
            self.transcript.add_speaker(member)
        self.transcript.speakers[member.name].start_speaking()

    @voice_recv.AudioSink.listener()
    def on_voice_member_speaking_stop(self, member):
        print(f"{member.name} stopped speaking")
        self.transcript.speakers[member.name].stop_speaking()

    def cleanup(self):
        print("Cleaning up streams")
        self.transcript.clear()
