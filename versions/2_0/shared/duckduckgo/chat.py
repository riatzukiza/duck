from duckduckgo_search import AsyncDDGS
import asyncio
import requests
import json

async def main():
    x = await AsyncDDGS().achat("Tell me about the stoics.")
    print(x)
    results = await AsyncDDGS().achat(f'Provide a list of keywords relavent to the inquery, respond with only valid json. {x}')
    print(results)

asyncio.run(main())
