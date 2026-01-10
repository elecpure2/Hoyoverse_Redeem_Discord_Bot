import asyncio
import aiohttp
import sys

# Force UTF-8 stdout
sys.stdout.reconfigure(encoding='utf-8')

async def main():
    urls = [
        ("GI_Artifact", "https://api.hakush.in/gi/data/ko/artifact.json"),
        ("GI_RelicSet", "https://api.hakush.in/gi/data/ko/relic_set.json"),
        ("GI_Relic", "https://api.hakush.in/gi/data/relic.json"), # Verified 404
        ("HSR_RelicSet", "https://api.hakush.in/hsr/data/kr/relic_set.json"),
        ("HSR_RelicSet_NoLang", "https://api.hakush.in/hsr/data/relic_set.json")
    ]
    
    async with aiohttp.ClientSession() as session:
        for name, url in urls:
            print(f"Checking {name}: {url}")
            try:
                async with session.get(url) as resp:
                    print(f"Status: {resp.status}")
            except Exception as e:
                print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
