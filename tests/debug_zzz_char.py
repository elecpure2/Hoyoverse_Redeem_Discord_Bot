
import aiohttp
import asyncio
import json

async def debug_zzz():
    async with aiohttp.ClientSession() as session:
        print("Fetching ZZZ characters...")
        async with session.get("https://api.hakush.in/zzz/data/character.json") as resp:
            data = await resp.json()
            print(f"Type: {type(data)}")
            
            found_miyabi = False
            
            iterable = data.items() if isinstance(data, dict) else enumerate(data)
            for k, v in iterable:
                # Print keys of first item
                if not found_miyabi:
                    print(f"Keys: {v.keys()}")
                
                # Search for Miyabi
                # English "Miyabi"? Korean "미야비"?
                # Check all values
                name_en = v.get('Name', '')
                name_kr = v.get('kr', '') or v.get('KR', '') or v.get('KO', '') or v.get('Ko', '')
                
                if "Miyabi" in name_en or "미야비" in str(v):
                    print(f"FOUND MIYABI: ID={k if isinstance(data, dict) else v.get('id')}")
                    print(f"Name EN: {name_en}")
                    print(f"Name KR: {name_kr}")
                    print(f"Raw Entry: {v}")
                    found_miyabi = True
                    break
            
            if not found_miyabi:
                print("Miyabi not found in list.")

if __name__ == "__main__":
    asyncio.run(debug_zzz())
