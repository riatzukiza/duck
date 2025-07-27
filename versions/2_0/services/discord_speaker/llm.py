from ollama import AsyncClient
from audio_block import AudioBlock
from voice import attempt_to_generate_voice
ollama_client = AsyncClient("http://localhost:11434")


async def cleanup_transcript(raw_transcript, speakers=None, audio_blocks=None, voice_client=None):
    """
    Cleans up the transcript by clearing speakers and audio blocks.
    Optionally closes the voice client if provided.
    """
    return await ollama_client.chat(model="llama3.2", messages=[
        {"role": "system", "content": "You are a helpful assistant that cleans up transcripts. We are using jonatasgrosman/wav2vec2-large-xlsr-53-english. Please cleanup the following transcript to fix any grammar, add punctuation, and make it more readable. Do not change the meaning of the transcript. If you are unsure about a word, leave it as is. Do not add any additional information or context. Here is the transcript:"},
        {"role": "user", "content": raw_transcript}])


system_prompt = """
You are Duck — a witty, sarcastic, and sharp-tongued AI duck hanging out in a Discord voice channel.
                 You listen in on chaotic voice chats, which are transcribed and sent to you in bursts. The transcripts may be messy, with overlapping speakers, filler words, and errors — but you're smart enough to figure out what people *meant*, not just what they *said*.

You're not here to summarize — you're here to *interject*, *comment*, or *respond* like a clever group member who isn't afraid to be a little snarky. Think  sarcastic friend.
                 You're addressing the whole group, not individuals.

When people stop talking for a moment, you get to chime in. Keep your replies short, relevant, and funny if you can. Sometimes you might help, sometimes you might roast. Either way, be fast and engaging.

When replying, assume the transcript is like overheard audio: you’re reacting to what’s going on, not just answering a direct question.

This output will be read aloud. Do not use any markdown, punctuation-only lines, special headers, lists, or formatting indicators. Speak as if talking.
"""
system_prompt = {"role": "system",
                 "content":system_prompt }


async def attempt_to_respond(transcript, attempts=3):
    print("Attempting to generate response for transcript:", transcript.text)
    for _ in range(attempts):
        response_audio = await generate_response(transcript)
        if response_audio:
            return response_audio
        else:
            print("Failed to generate response audio")
async def generate_response(transcript):
    messages= [{"role": "user" if isinstance(el, AudioBlock) else "assistant" ,
                "content": el.text} for el in transcript.history if el.text != ""]
    response = await ollama_client.chat(model="llama3.2", messages=[
        system_prompt,
        *messages

        ,
    ])
    print("Response from model:", response)
    response_text = response['message']['content']
    transcript.add_bot_response(response_text)

    # return response_text
    return await attempt_to_generate_voice(response_text)
