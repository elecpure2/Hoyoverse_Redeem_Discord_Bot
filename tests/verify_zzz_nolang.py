import asyncio
import aiohttp
import sys

# Force UTF-8 stdout
sys.stdout.reconfigure(encoding='utf-8')

async def main():
    urls = [
        "https://api.hakush.in/zzz/data/weapon.json",
        "https://api.hakush.in/zzz/data/character.json"
    ]
    
    async with aiohttp.ClientSession() as session:
        for url in urls:
            print(f"Checking {url}")
            try:
                async with session.get(url) as resp:
                    print(f"Status: {resp.status}")
                    if resp.status == 200:
                        data = await resp.json()
                        count = 0
                        if isinstance(data, dict):
                            keys = list(data.keys())
                            print(f"Keys sample: {keys[:5]}")
                            # check content
                            v = data[keys[0]]
                            print(f"Sample Val: {v}")
                        elif isinstance(data, list):
                            print(f"List len: {len(data)}")
                            if data: print(f"Sample: {data[0]}")
            except Exception as e:
                print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
