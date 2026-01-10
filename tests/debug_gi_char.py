
import aiohttp
import asyncio
import json

async def debug_gi_char():
    async with aiohttp.ClientSession() as session:
        print("Fetching GI character list...")
        async with session.get("https://api.hakush.in/gi/data/character.json") as resp:
            data = await resp.json()
            if isinstance(data, list):
                print(f"First item: {data[0]}")
            elif isinstance(data, dict):
                k = list(data.keys())[0]
                print(f"First item: {data[k]}")

if __name__ == "__main__":
    asyncio.run(debug_gi_char())
