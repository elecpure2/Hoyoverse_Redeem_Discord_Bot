import aiohttp
import asyncio
import json

async def main():
    async with aiohttp.ClientSession() as s:
        # GI artifact detail structure
        print("=== GI Artifact Detail ===")
        async with s.get("https://api.hakush.in/gi/data/ko/artifact/15043.json") as r:
            data = await r.json()
            print(json.dumps(data, indent=2, ensure_ascii=False)[:2000])
        
        # HSR relicset detail structure  
        print("\n=== HSR Relicset Detail ===")
        async with s.get("https://api.hakush.in/hsr/data/kr/relicset/129.json") as r:
            data = await r.json()
            print(json.dumps(data, indent=2, ensure_ascii=False)[:2000])

asyncio.run(main())
