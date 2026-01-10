
import aiohttp
import asyncio
import json
import re

# Mock clean_description for independent testing
def clean_description(text: str, params=None) -> str:
    if not text: return ""
    text = re.sub(r'<[^>]+>', '', text)
    if params:
        def replace_param(match):
            idx = int(match.group(1)) - 1
            if 0 <= idx < len(params):
                return str(params[idx])
            return match.group(0)
        text = re.sub(r'#(\d+)\[([a-zA-Z0-9]+)\](%?)', replace_param, text)
    text = text.replace(r'\n', '\n')
    text = re.sub(r'\{LINK#.+?\}(.+?)\{/LINK\}', r'\1', text)
    return text

async def debug_zzz():
    print("--- Debugging ZZZ Data ---")
    
    async with aiohttp.ClientSession() as session:
        # 1. Check Item JSON
        print("\n[1] Fetching ZZZ Item JSON...")
        async with session.get("https://api.hakush.in/zzz/data/ko/item.json") as resp:
            if resp.status != 200:
                print(f"Failed to fetch item.json: {resp.status}")
            else:
                items = await resp.json()
                print(f"Total Items: {len(items)}")
                # Sample a known ID if possible or first few
                # Miyabi mats: 100223, 100233, 100213
                samples = ['100223', '100233', '100213']
                for sid in samples:
                    if sid in items:
                        print(f"Item {sid}: {items[sid]}")
                    else:
                        # Try int key
                        if int(sid) in items:
                             print(f"Item (int) {sid}: {items[int(sid)]}")
                        else:
                             print(f"Item {sid} NOT FOUND")
                
                # Check keys of random item
                first_k = list(items.keys())[0]
                print(f"Sample Item [{first_k}]: {items[first_k]}")

        # 2. Check Character Raw Data
        char_id = 1251 # Miyabi
        url = f"https://api.hakush.in/zzz/data/ko/character/{char_id}.json"
        print(f"\n[2] Fetching Character {char_id} Raw Data...")
        
        async with session.get(url) as resp:
            if resp.status != 200:
                print(f"Failed to fetch char data: {resp.status}")
                return
            
            raw_data = await resp.json()
            print(f"Keys: {list(raw_data.keys())}")
            
            # Check Materials (Ascension/Stats)
            stats = raw_data.get('Stats', {})
            print(f"Stats keys: {list(stats.keys())}")
            # Check Cost in Stats
            # Usually 'Promotion'?
            
            # Check Skills
            skills = raw_data.get('Skill', {})
            print(f"Skills Type: {type(skills)}")
            if isinstance(skills, dict):
                print(f"Skill Count: {len(skills)}")
                for k, v in list(skills.items())[:3]:
                    print(f"Skill [{k}] Keys: {list(v.keys())}")
                    print(f"Skill [{k}] Raw: {v}")
                    
                    # Check for name/desc with lowercase?
                    name = v.get('Name') or v.get('name')
                    desc = v.get('Desc') or v.get('desc')
                    desc2 = v.get('Desc2') or v.get('desc2')
                    print(f"  -> Name: {name}, Desc: {desc}, Desc2: {desc2}")
            elif isinstance(skills, list):
                print(f"Skill List Count: {len(skills)}")
                if skills:
                    print(f"Skill 0: {skills[0]}")
            else:
                print("Skills empty or wrong type")

if __name__ == "__main__":
    asyncio.run(debug_zzz())
