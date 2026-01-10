
import aiohttp
import asyncio
import json

async def debug_gi_search():
    async with aiohttp.ClientSession() as session:
        print("Fetching GI weapon list...")
        async with session.get("https://api.hakush.in/gi/data/weapon.json") as resp:
            if resp.status != 200:
                print(f"Failed: {resp.status}")
                return
            
            try:
                data = await resp.json()
                print(f"Data type: {type(data)}")
                if isinstance(data, list):
                    print(f"List length: {len(data)}")
                    print(f"First item: {data[0]}")
                elif isinstance(data, dict):
                    print(f"Dict keys count: {len(data)}")
                    first_k = list(data.keys())[0]
                    print(f"First item [{first_k}]: {data[first_k]}")
                
                # Search for target
                target = "막간의 야상곡"
                found = False
                
                # Iterate and search
                iterable = data.items() if isinstance(data, dict) else enumerate(data)
                for k, v in iterable:
                    # In list, v is the item. In dict, v is the value.
                    # Normalized check
                    name = v.get('kr') or v.get('Name') or v.get('KO')
                    if name and (target in name or "야상곡" in name):
                        print(f"FOUND: {name} (ID: {v.get('id') if isinstance(data, list) else k})")
                        print(f"Raw Entry: {v}")
                        found = True
                
                if not found:
                    print("Target not found in data.")
                    
            except Exception as e:
                print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(debug_gi_search())
