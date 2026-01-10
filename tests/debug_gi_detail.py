
import aiohttp
import asyncio
import json

async def debug_gi_detail():
    # Fetch list first
    list_url = "https://api.hakush.in/gi/data/kr/character.json"
    target_id = None
    
    async with aiohttp.ClientSession() as session:
        print("Fetching List...")
        async with session.get(list_url) as resp:
             if resp.status == 200:
                 data = await resp.json()
                 print(f"List Keys Sample: {list(data.keys())[:5]}")
                 k0 = list(data.keys())[0]
                 print(f"Sample Entry [{k0}]: {data[k0]}")

                 # Find Zhongli or anyone
                 for k, v in data.items():
                     val = v
                     if isinstance(v, str): val = {'KR': v} # sometimes just name?
                     # Check v type
                     
                     name = val.get('KR') or val.get('name') or val.get('Name') or str(val)
                     if '종려' in str(name):
                         target_id = k
                         print(f"Found Zhongli: {k}")
                         break
                     if not target_id: target_id = k # Fallback
    
    if not target_id:
        print("No ID found")
        return

    detail_url = f"https://api.hakush.in/gi/data/kr/character/{target_id}.json"
    
    async with aiohttp.ClientSession() as session:
        print(f"Fetching {target_id}...")
        async with session.get(detail_url) as resp:
            if resp.status != 200:
                print(f"Failed: {resp.status}")
                return
            data = await resp.json()
            print(f"Keys: {data.keys()}")
            
            # Ascension logic?
            # It seems GI raw data separates character info and material info?
            # Actually hakushin usually puts 'ascension' in detail if using library.
            # But Raw JSON might differ.
            # Let's check 'promote' or similar.
            
            # Check 'Costumes'
            if 'Costumes' in data:
                 print(f"Costumes: {data['Costumes']}")
            
            # Dump full keys
            # to see where materials are.


if __name__ == "__main__":
    asyncio.run(debug_gi_detail())
