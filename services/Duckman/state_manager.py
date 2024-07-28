from shared import settings
from state import update_state,state
from discord_client import client
import asyncio
from shared.create_message_embeddings import update_embeddings
from discussion import generate_channel_state


running=False
@client.event
async def on_ready():
    global running
    print(f'Logged in as {client.user}')
    # await clear_answers(timmy_answer_cache_collection)
    update_state({"new_message":""})
    # running=True
    while running:
        await generate_channel_state(state.get("channel_id",settings.DEFAULT_CHANNEL))
        await asyncio.sleep(1)