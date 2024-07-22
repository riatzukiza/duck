import json
from litellm import acompletion


async def async_complete(context, format=None,temperature=0.9):
    response=await acompletion(
        model="ollama_chat/llama3",
        messages=context,
        max_tokens=8192,
        api_base="http://ollama:11434",
        format="json" if format=="json" else None,
    )
    string=response.choices[0].message.tool_calls[0].function.arguments if format=="json" else response.choices[0].message.content
    return json.loads(string) if format=="json" else string