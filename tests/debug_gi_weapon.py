
import aiohttp
import asyncio
import json

async def debug_gi_structure():
    async with aiohttp.ClientSession() as session:
        # GI: Try a known weapon like "Mistplitter Reforged" (11509) or "Amenoma Kageuchi" (11413) 
        # or the one from before 11417 (Sapwood Blade).
        gi_id = 11417 # Sapwood Blade
        print(f"Fetching GI Weapon {gi_id}...")
        async with session.get(f"https://api.hakush.in/gi/data/ko/weapon/{gi_id}.json") as resp:
            data = await resp.json()
            print(f"Keys: {list(data.keys())}")
            # Look for description-like fields
            for k, v in data.items():
                if isinstance(v, (dict, list)) and 'Desc' in str(v):
                    print(f"Potential Desc Field [{k}]: {str(v)[:200]}...")
            
            # Check for 'Skill' or 'EquipAffix' equivalent
            if 'Skill' in data: print(f"Skill: {data['Skill']}")
        
        # Search for '달빛'
        print("\nSearching for '달빛'...")
        async with session.get("https://api.hakush.in/gi/data/weapon.json") as resp:
            data = await resp.json()
            for k, v in data.items():
                name = v.get('kr') or v.get('Name')
                if name and '달빛' in name:
                    print(f"Found: {name} (ID: {k})")

if __name__ == "__main__":
    asyncio.run(debug_gi_structure())
