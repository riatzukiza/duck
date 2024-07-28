from shared import settings
from state import update_state,state
from shared.discord import send_message, split_markdown
from sent_messages import sent_messages
from discord_client import client

async def handle_chunk(chunk,stream_id,finished=False):
    stream_key='current_text:'+stream_id
    if finished or state.get("new_message","")!="":
        split=split_markdown(state.get(stream_key,""),finished=True)
        update_state({ "new_message":"" })
        await send_message({ 
                "content":split[0], 
                "channel": state.get("channel_id",settings.DEFAULT_CHANNEL)
            },
            sent_messages,
            client,
            mark_sent=False
        )
        return chunk
    update_state({ stream_key: state.get(stream_key,"")+chunk })

    split=split_markdown(state.get(stream_key,""))

    if len(split)>1:
        await send_message({ "content":split[0], "channel":state['channel_id'] },sent_messages,client,mark_sent=False)
        update_state({ stream_key: "".join(split[1:]) })