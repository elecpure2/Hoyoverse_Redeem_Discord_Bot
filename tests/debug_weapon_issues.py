
import aiohttp
import asyncio
import json
import re

async def debug_weapon():
    async with aiohttp.ClientSession() as session:
        # HSR: 눈물의 흔적 (Traces of Tears? Or colloquial? Let's search '눈물의 흔적')
        # Actually user said "눈물의 흔적". Let's try to find its ID first or just pick a known LC with params.
        # "Alone along the Deep" or similar?
        # Let's search known HSR LC ID for testing params. ID: 21001 (Collapsing Sky) or 23001 (Night on the Milky Way).
        # Let's try to find '눈물의 흔적' in HSR cache if possible, or just use a generic one.
        
        # 1. HSR Parameter Parsing
        print("--- HSR Param Test ---")
        lc_id = 23001 # Night on the Milky Way
        async with session.get(f"https://api.hakush.in/hsr/data/kr/lightcone/{lc_id}.json") as resp:
            data = await resp.json()
            skill = data.get('Refinements') or data.get('Skill')
            print(f"HSR Skill Keys: {skill.keys() if skill else 'None'}")
            if skill and 'Level' in skill:
                 l1 = skill['Level']['1']
                 desc = skill['Desc']
                 params = l1['ParamList']
                 print(f"Raw Desc: {desc}")
                 print(f"Params: {params}")
        
        # 2. GI Weapon Effect (Affix)
        print("\n--- GI Affix Test ---")
        # 막간의 야상곡 (Mitternachts Waltz?) ID: 15413
        # 신월의 달빛 (Xiphos' Moonlight) ID: 11417
        gi_id = 11417 
        async with session.get(f"https://api.hakush.in/gi/data/ko/weapon/{gi_id}.json") as resp:
            if resp.status == 200:
                data = await resp.json()
                print(f"Name: {data.get('Name')}")
                print(f"Affix Keys: {data.get('Affix', {}).keys() if data.get('Affix') else 'None'}")
                if data.get('Affix'):
                    print(f"Affix Data: {json.dumps(data.get('Affix'), ensure_ascii=False)[:300]}...")
            else:
                 print(f"Failed to fetch GI Weapon {gi_id}")

        # 3. Cache Search Test for '신월의 달빛'
        print("\n--- Cache Test ---")
        async with session.get("https://api.hakush.in/gi/data/weapon.json") as resp:
            data = await resp.json()
            found = False
            for k, v in data.items():
                name = v.get('kr') or v.get('Name')
                if name == "신월의 달빛" or "신월" in name:
                    print(f"Found in Cache: {name} (ID: {k})")
                    found = True
            if not found: print("신월의 달빛 NOT found in cache.")

if __name__ == "__main__":
    asyncio.run(debug_weapon())
