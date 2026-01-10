import asyncio
import aiohttp
import sys

# Force UTF-8 stdout
sys.stdout.reconfigure(encoding='utf-8')

async def main():
    url = "https://api.hakush.in/zzz/data/weapon.json"
    print(f"Checking {url}")
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    # Check first 5 items for KO field
                    count = 0
                    for k, v in data.items():
                        print(f"ID: {k}")
                        print(f"  EN: {v.get('EN')}")
                        print(f"  KO: {v.get('KO')}")
                        print(f"  CHS: {v.get('CHS')}")
                        count += 1
                        if count >= 5: break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
