
import sys
import numpy as np
import soundfile as sf
from openvino.runtime import Core
from models.forward_tacotron_ie import ForwardTacotronIE
from models.mel2wave_ie import WaveRNNIE
from time import perf_counter
from split_sentances import split_sentences
import re
import sys
import numpy as np
import soundfile as sf
from split_sentances import split_sentences
import numpy as np
import io
import wave
import discord
from scipy.signal import resample_poly

import torch
import torchaudio
import torch.nn.functional as F


# Load pre-trained model
model = Wav2Vec2ForCTC.from_pretrained("facebook/wav2vec2-base-960h")
processor = Wav2Vec2Processor.from_pretrained("facebook/wav2vec2-base-960h")

# Setup
core = Core()
device = "NPU"
# === Load models ===
forward_tacotron = ForwardTacotronIE(
    "models/public/forward-tacotron/forward-tacotron-duration-prediction/FP16/forward-tacotron-duration-prediction.xml",
    "models/public/forward-tacotron/forward-tacotron-regression/FP16/forward-tacotron-regression.xml",
    core,
    device,
)

vocoder = WaveRNNIE(
    "models/public/wavernn/wavernn-upsampler/FP16/wavernn-upsampler.xml",
    "models/public/wavernn/wavernn-rnn/FP16/wavernn-rnn.xml",
    core,
    device=device,
    upsampler_width=512,  # Adjust as needed
    target=1000,  # Adjust as needed
    # target=200,
    overlap=500,
    hop_length=100,  # Adjust as needed
)
def transcribe_long_waveform(waveform, batch_size=2):
    """
    Transcribes a long audio file by splitting it into smaller batches.
    """
    waveform_resampled = torchaudio.transforms.Resample(orig_freq=sample_rate, new_freq=16000)(waveform)
    batches= split_waveform_into_batches(waveform_resampled, chunk_size=320000)

    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, 'wb') as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)  # 2 bytes for int16
        wf.setframerate(48000)
        wf.writeframes(int16_data.tobytes())
    wav_buffer.seek(0)

    result=[]
    for batch in batches:
        ov_out=compiled_model([batch])
        logits= torch.tensor(ov_out['logits'])
        predicted_ids = torch.argmax(logits, dim=-1)
        transcription=processor.batch_decode(predicted_ids)
        print("batch transcription", transcription)
        result.append(transcription[0] if isinstance(transcription, list) else transcription)
    return " ".join(result)



def generate_voice_fragment(text):
    return vocoder.forward(forward_tacotron.forward(text.strip(), alpha=1.0))

def generate_voice(text):
    """
    Generates voice from the given text using the forward_tacotron and vocoder models.
    """
    return [generate_voice_fragment(chunk) for chunk in split_sentences(text) if chunk]
