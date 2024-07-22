import json
from litellm import acompletion
from litellm import acompletion

async def async_complete(context, format=None,temperature=0.9,streaming=False,streaming_callback=None):
    response=await acompletion(
        model="ollama_chat/llama3",
        messages=context,
        max_tokens=8192,
        api_base="http://192.168.0.23:11434",
        # api_base="http://ollama:11434",
        format="json" if format=="json" else None,
        stream=streaming,
    )
    default_result=""
    if streaming and streaming_callback:
        async for chunk in response:
            text=chunk.choices[0].delta.content

            if text: 
                default_result+=text
                callback_result=await streaming_callback(text,finished=False)
                if callback_result:
                    return streaming_callback(default_result,finished=True)

            else: 
                # the last chunk will be the full string.
                return await streaming_callback(default_result,finished=True)

    string=response.choices[0].message.tool_calls[0].function.arguments if format=="json" else response.choices[0].message.content

    return json.loads(string) if format=="json" else string