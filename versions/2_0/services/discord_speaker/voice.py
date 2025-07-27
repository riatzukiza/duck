import io
from lib.utils.split_sentances import split_sentences
import aiohttp
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
async def voice_generator(text,url='http://localhost:5002/synth_voice'):
    print("Generating voice for text:", text)
    sentences = split_sentences(text)
    for sentence in sentences:
        data = {
            "input_text": sentence
        }
        audio_chunk = await attempt_to_generate_voice( data)
        if audio_chunk:
            yield wrap_pcm_in_wav(audio_chunk)
        else:
            print("Failed to generate audio for sentence:", sentence)
async def generate_voice(text, url='http://localhost:5002/synth_voice'):
    print("Generating voice for text:", text)
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


async def attempt_to_generate_voice(text, attempts=3):
    print("Attempting to generate voice for text:", text)
    for _ in range(attempts):
        response_audio = await generate_voice(text)
        if response_audio:
            print(f"Successfully generated voice audio for text: {text[:30]}...")
            return response_audio
        else:
            print("Failed to generate voice audio")
    return None
