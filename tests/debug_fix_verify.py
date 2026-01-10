
import asyncio
import aiohttp
import os

# Suppress loguru
os.environ["LOGURU_LEVEL"] = "CRITICAL"

async def debug_verify():
    # 1. Fetch Item Name
    item_id = 110263
    url = f'https://api.hakush.in/hsr/data/kr/item/{item_id}.json'
    print(f"Fetching Item {item_id} from {url}...")
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            print(f"Status: {resp.status}")
            if resp.status == 200:
                data = await resp.json()
                print(f"Name: {data.get('Name')}")
            else:
                print("Failed to fetch item.")

    # 2. Fetch Character Stats for Sparkle
    char_id = 1306
    url_char = f'https://api.hakush.in/hsr/data/kr/character/{char_id}.json'
    print(f"\nFetching Character {char_id}...")
    async with aiohttp.ClientSession() as session:
        async with session.get(url_char) as resp:
            if resp.status == 200:
                data = await resp.json()
                
                # Check specific stat keys mentioned by user
                print("\nChecking keys in Stats/Relics/Trace:")
                # Relics
                relics = data.get('Relics', {})
                props = relics.get('PropertyList', [])
                for p in props:
                    print(f"MainStat Key: {p.get('PropertyType')}")
                
                subprops = relics.get('SubAffixPropertyList', [])
                print(f"SubStat Keys: {subprops}")
                
                # Trace keys
                skill_trees = data.get('SkillTrees', {})
                for point in skill_trees.values():
                    if isinstance(point, dict):
                        for level in point.values():
                            if isinstance(level, dict):
                                for s in level.get('StatusAddList', []):
                                    print(f"Trace Stat Key: {s.get('PropertyType')}")
                                break # Check one level
            else:
                print("Failed to fetch character.")

if __name__ == "__main__":
    asyncio.run(debug_verify())
