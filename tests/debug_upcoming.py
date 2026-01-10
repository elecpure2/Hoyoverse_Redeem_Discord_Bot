import asyncio
import aiohttp
import sys
import os
sys.path.append(os.getcwd())
from cogs.hakushin import HakushinAPI, Game, Language

async def main():
    print("--- Debugging Genshin Upcoming Characters ---")
    async with HakushinAPI(Game.GI, Language.KO) as client:
        new_items = await client.fetch_new()
        char_ids = getattr(new_items, 'character_ids', [])
        print(f"Found {len(char_ids)} new characters.")
        
        for char_id in char_ids[:5]:
            print(f"\n[ID: {char_id}] Fetching detail...")
            char = await client.fetch_character_detail(char_id)
            print(f"Name: {char.name}")
            print(f"Element (Attribute): {getattr(char, 'element', 'N/A')}")
            
            # Fetch Raw Data to check element key
            url = f'https://api.hakush.in/gi/data/kr/character/{char_id}.json'
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        raw = await resp.json()
                        print(f"Raw Element: {raw.get('Element')}")
                        print(f"Raw element: {raw.get('element')}")
                    else:
                        print(f"Raw Data Fetch API Status: {resp.status}")

if __name__ == "__main__":
    asyncio.run(main())
