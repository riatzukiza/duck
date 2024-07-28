import asyncio
import random

from shared.discord import get_latest_channel_docs

from shared import settings

from state import update_state_from_search,state

async def main():
    while True:
        messages=get_latest_channel_docs(state.get("channel_id",settings.DEFAULT_CHANNEL))
        choice=random.choice(messages)
        await update_state_from_search(
            choice['content'],
            "random_message"
        )
        await asyncio.sleep(60)

asyncio.run(main())