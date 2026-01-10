import asyncio
import aiohttp
import sys

# Force UTF-8 stdout
sys.stdout.reconfigure(encoding='utf-8')

async def main():
    # Known IDs from previous run
    targets = [
        ("gi", "weapon", "11519"),
        ("zzz", "weapon", "14149")
    ]
    
    async with aiohttp.ClientSession() as session:
        for game, endpoint, wid in targets:
            print(f"--- Checking {game} {wid} ---")
            for lang in ["kr", "ko"]:
                url = f"https://api.hakush.in/{game}/data/{lang}/{endpoint}/{wid}.json"
                try:
                    async with session.get(url) as resp:
                        print(f"Lang '{lang}': {resp.status}")
                        if resp.status == 200:
                            data = await resp.json()
                            print(f"Name: {data.get('Name') or data.get('kr')}")
                except Exception as e:
                    print(f"Error {lang}: {e}")

if __name__ == "__main__":
    asyncio.run(main())
