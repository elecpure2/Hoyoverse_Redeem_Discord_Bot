import asyncio
import aiohttp
import json
import sys

# Force UTF-8 stdout
sys.stdout.reconfigure(encoding='utf-8')

async def main():
    games = [
        ("gi", "https://api.hakush.in/gi/new.json"),
        ("hsr", "https://api.hakush.in/hsr/new.json"),
        ("zzz", "https://api.hakush.in/zzz/new.json")
    ]
    
    async with aiohttp.ClientSession() as session:
        for game, url in games:
            print(f"--- Checking {game} ---")
            try:
                async with session.get(url) as resp:
                    print(f"Status: {resp.status}")
                    if resp.status == 200:
                        data = await resp.json()
                        print(f"Keys: {list(data.keys())}")
                        
                        # Check weapon/lightcone keys
                        w_ids = []
                        if game == 'gi': w_ids = data.get('weapon', [])
                        elif game == 'hsr': w_ids = data.get('lightcone', [])
                        elif game == 'zzz': w_ids = data.get('weapon', []) # ZZZ might use weapon or w_engine?
                        
                        print(f"Weapon IDs: {w_ids}")
                        
                        # Try fetching one weapon detail raw to see structure
                        if w_ids:
                            wid = w_ids[0]
                            type_path = "weapon"
                            if game == 'hsr': type_path = "lightcone"
                            # ZZZ might be weapon?
                            
                            detail_url = f"https://api.hakush.in/{game}/data/kr/{type_path}/{wid}.json"
                            print(f"Fetching detail: {detail_url}")
                            async with session.get(detail_url) as d_resp:
                                if d_resp.status == 200:
                                    d_data = await d_resp.json()
                                    # Print Name and Type fields
                                    print(f"Name: {d_data.get('Name') or d_data.get('kr')}") # ZZZ might use different
                                    print(f"Type/Path: {d_data.get('Weapon') or d_data.get('Path') or d_data.get('Profession')}") 
                                    print(f"Keys in detail: {list(d_data.keys())[:10]}")
                                else:
                                    print(f"Detail fetch failed: {d_resp.status}")

            except Exception as e:
                print(f"Error: {e}")
            print("\n")

if __name__ == "__main__":
    asyncio.run(main())
