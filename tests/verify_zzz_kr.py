import asyncio
import aiohttp
import sys

# Force UTF-8 stdout
sys.stdout.reconfigure(encoding='utf-8')

async def main():
    endpoints = [
        "https://api.hakush.in/zzz/data/ko/weapon.json",
        "https://api.hakush.in/zzz/data/kr/weapon.json"
    ]
    
    async with aiohttp.ClientSession() as session:
        for url in endpoints:
            print(f"Checking {url}")
            try:
                async with session.get(url) as resp:
                    print(f"Status: {resp.status}")
                    if resp.status == 200:
                        data = await resp.json()
                        # check a few items for Korean Chars
                        count = 0
                        for k, v in data.items():
                            name = v.get('Name') or v.get('kr') or ""
                            # Check for Korean char range
                            has_korean = any(ord('가') <= ord(c) <= ord('힣') for c in name)
                            print(f"  {k}: {name} (Korean? {has_korean})")
                            count += 1
                            if count > 3: break
            except Exception as e:
                print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
