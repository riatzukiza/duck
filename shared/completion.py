import json
import uuid
import ollama

async def async_complete(context,provider="http://ollama-gpu:11434", format=None,temperature=0.9,streaming=False,streaming_callback=None):
    try:
        client=ollama.AsyncClient(host=provider)
        for message in context:
            print(message['content'])
        response=await client.chat(
            model="Godmoded/llama3-lexi-uncensored",
            #model="llama3.1",
            messages=context,
            format="json" if format=="json" else None,
            stream=streaming,
        )
        if streaming and streaming_callback:
            stream_id=str(uuid.uuid4())
            result=""
            async for chunk in response:
                text=chunk['message']['content']
                if text: 
                    result+=text
                    done=await streaming_callback(text,stream_id,finished=False)
                    if done: 
                        break

                else: 
                    # the last chunk will be the full string.
                    return await streaming_callback(result,stream_id,finished=True)
        else:
            string=response['message']['content']
            return json.loads(string) if format=="json" else string
            
    except Exception as e:
        print("Error in async_complete")
        print(e)
        raise e



