
import asyncio
import ollama


embeddings={}
async def generate_embedding(text):
    print("embedding")
    print(text)
    OLLAMA_API_URL = "http://ollama-gpu:11434"
    MODEL_NAME = "all-minilm"

    if text in embeddings:
        print("cached")
        return embeddings[text]

    client=ollama.AsyncClient(host=OLLAMA_API_URL)
    try:
        response = await client.embeddings(
            model=MODEL_NAME,
            prompt=text
        )
    except Exception as e:
        print("There was an issue embedding the text.")
        print(e)
        await asyncio.sleep(5)
        return await generate_embedding(text)
    embeddings[text]=response["embedding"]
    return response["embedding"]