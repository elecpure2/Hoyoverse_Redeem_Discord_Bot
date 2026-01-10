import asyncio
import aiohttp
import sys

# Force UTF-8 stdout
sys.stdout.reconfigure(encoding='utf-8')

async def main():
    urls = [
        ("GI", "https://api.hakush.in/gi/data/ko/relic.json"),
        ("HSR", "https://api.hakush.in/hsr/data/kr/relic.json"),
        ("ZZZ", "https://api.hakush.in/zzz/data/equipment.json") 
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
                                name = v.get('Name') or v.get('kr') or v.get('KO') or v.get('EN')
                                print(f"  {k}: {name}")
                                count += 1
                                if count >= 3: break
                        elif isinstance(data, list):
                            # GI list?
                            print("  List type")
                            for item in data[:3]:
                                print(f"  {item}")
            except Exception as e:
                print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
