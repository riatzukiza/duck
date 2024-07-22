import asyncio
import json
import uuid
import random
from litellm import acompletion
from litellm import acompletion

complete_providers=[
        "http://192.168.0.27:11434",
        "http://192.168.0.23:11434",
        "http://ollama:11434",
]
active_provider_requests={}

for provider in complete_providers:
    active_provider_requests[provider]=0

async def async_complete(context, format=None,temperature=0.9,streaming=False,streaming_callback=None):

    random_api_base=random.choice(complete_providers)

    print(f"Using API base: {random_api_base}")

    while active_provider_requests[random_api_base] > 5:
        await asyncio.sleep(1)
    
    active_provider_requests[random_api_base]+=1

    response=await acompletion(
        model="ollama_chat/llama3",
        messages=context,
        max_tokens=8192,
        api_base=random_api_base,
        format="json" if format=="json" else None,
        stream=streaming,
    )
    if streaming and streaming_callback:
        stream_id=str(uuid.uuid4())
        default_result=""
        async for chunk in response:
            text=chunk.choices[0].delta.content
            if text: 
                default_result+=text
                callback_result=await streaming_callback(text,stream_id,finished=False)
                if callback_result:
                    return default_result

            else: 
                # the last chunk will be the full string.
                return await streaming_callback(default_result,stream_id,finished=True)

    string=response.choices[0].message.tool_calls[0].function.arguments if format=="json" else response.choices[0].message.content

    active_provider_requests[random_api_base]-=1

    return json.loads(string) if format=="json" else string

