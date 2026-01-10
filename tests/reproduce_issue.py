import asyncio
import aiohttp
import json
import sys

# Force UTF-8 encoding for stdout
sys.stdout.reconfigure(encoding='utf-8')

async def main():
    print("Testing HSR Character Fetch via Raw HTTP...")
    url = "https://api.hakush.in/hsr/data/character.json"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                print(f"Status: {resp.status}")
                if resp.status == 200:
                    data = await resp.json()
                    print(f"Keys in response: {list(data.keys())[:10] if isinstance(data, dict) else 'List'}")
                    
                    if isinstance(data, dict):
                         print(f"Count: {len(data)}")
                         first_key = list(data.keys())[0]
                         print(f"Sample ({first_key}) 'kr': {data[first_key].get('kr')}")
                         
                         # Check other IDs
                         target_ids = ['1001', '1002', '1003', '1102', '1303']
                         for ch_id in target_ids:
                             if ch_id in data:
                                 name = data[ch_id].get('kr')
                                 print(f"ID {ch_id} 'kr': {name}")
                    else:
                        print("Data is not a dict")

    except Exception as e:
        print(f"Error fetching raw HSR characters: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
