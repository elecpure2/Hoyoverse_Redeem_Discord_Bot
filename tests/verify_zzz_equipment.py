import asyncio
import aiohttp
import sys

# Force UTF-8 stdout
sys.stdout.reconfigure(encoding='utf-8')

async def main():
    url = "https://api.hakush.in/zzz/data/ko/equipment.json"
    print(f"Checking {url}")
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as resp:
                print(f"Status: {resp.status}")
                if resp.status == 200:
                    data = await resp.json()
                    count = 0
                    for k, v in data.items():
                        print(f"ID: {k}, Name: {v.get('Name') or v.get('KO')}")
                        count += 1
                        if count >= 3: break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
