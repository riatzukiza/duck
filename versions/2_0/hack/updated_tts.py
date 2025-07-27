
import sys
import numpy as np
import soundfile as sf
from openvino.runtime import Core
from models.forward_tacotron_ie import ForwardTacotronIE
from models.mel2wave_ie import WaveRNNIE
from time import perf_counter
from split_sentances import split_sentences
import re

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
    # target=100,  # Adjust as needed
    # target=200,
    # overlap=50
)

# === Inference Pipeline ===
input_text = """hello world, testing long input? let's try more, How are you? How is your day going, how is the weather today? This is a test of the text to speech system, it should handle multiple sentences and punctuation marks correctly. Let's see how it performs with longer sentences and various punctuation!

We're gonna add a new line in to see how it handles that. The quick brown fox jumps over the lazy dog.

This is a longer sentence to test the splitting functionality.

It should be split into multiple chunks if it exceeds the maximum length.

Let's see how it works with punctuation, like commas, periods, and question marks!
Also, let's add some more text to ensure we hit the max length limit.
This should help us verify that the sentence splitting works as expected.

We need a really really really long sentance without any punctuation marks to test the word level splitting correctly hopefully this will work out well and we can see how the system handles it without any breaks or pauses in the text.
"""

def generate_voice_fragment(text):
    return vocoder.forward(forward_tacotron.forward(text.strip(), alpha=1.0))
def generate_voice(text):
    """
    Generates voice from the given text using the forward_tacotron and vocoder models.
    """
    return [generate_voice_fragment(chunk) for chunk in split_sentences(text) if chunk]

# === Save output ===
sf.write("output.wav", generate_voice(input_text), 22050)
print("Audio saved to output.wav")
