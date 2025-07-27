
import sys
import numpy as np
import soundfile as sf
from openvino.runtime import Core
from models.forward_tacotron_ie import ForwardTacotronIE
from models.mel2wave_ie import WaveRNNIE
from time import perf_counter

# Setup
core = Core()
device = "NPU"

# Simple text to ID mapping
alphabet = " abcdefghijklmnopqrstuvwxyz'"
char2id = {c: i+1 for i, c in enumerate(alphabet)}
def text_to_sequence(text):
    text = text.lower()
    return [char2id.get(c, 0) for c in text if c in char2id]

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
    # target=200,
    # overlap=10
)

# === Inference Pipeline ===
time_start = perf_counter()
input_text = "Hello world, this is a test how are you?"

mel = forward_tacotron.forward(input_text, alpha=1.0)
audio = vocoder.forward(mel)
time_end = perf_counter()

# === Save output ===
sf.write("output.wav", audio, 22050)
print("Audio saved to output.wav")
print("Inference time: {:.2f} seconds".format(time_end - time_start))
