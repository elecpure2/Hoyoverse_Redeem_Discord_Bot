import asyncio
import aiohttp
import sys

# Force UTF-8 stdout
sys.stdout.reconfigure(encoding='utf-8')

async def main():
    urls = [
        ("GI", "https://api.hakush.in/gi/data/relic.json"),
        ("HSR", "https://api.hakush.in/hsr/data/relic.json")
    ]
    
    async with aiohttp.ClientSession() as session:
        for game, url in urls:
            print(f"Checking {game}: {url}")
            try:
                async with session.get(url) as resp:
                    print(f"Status: {resp.status}")
                    if resp.status == 200:
                        data = await resp.json()
                        count = 0
                        if isinstance(data, dict):
                            for k, v in data.items():
                                # Try KO/kr/CJK
                                name = v.get('Name')
                                kr = v.get('kr') or v.get('KO')
                                print(f"  ID: {k}")
                                if kr: print(f"    KR: {kr}")
                                if name: print(f"    Name: {name}")
                                keys = list(v.keys())
                                print(f"    Keys: {keys[:5]}")
                                count += 1
                                if count >= 3: break
            except Exception as e:
                print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
