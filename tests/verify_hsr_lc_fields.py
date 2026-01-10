import asyncio
import aiohttp
import sys

# Force UTF-8 stdout
sys.stdout.reconfigure(encoding='utf-8')

async def main():
    # ID for "She decided to watch..." (그녀가 보기로 결심했을 때)
    # verify_lang.py (Step 171) said ID 23028 had empty Desc.
    url = "https://api.hakush.in/hsr/data/kr/lightcone/23028.json"
    
    print(f"Checking {url}")
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as resp:
                print(f"Status: {resp.status}")
                if resp.status == 200:
                    data = await resp.json()
                    # Print all keys regarding description
                    for k, v in data.items():
                        if k == 'Refinements':
                            print(f"Refinements: {v}")
                        elif 'Desc' in k or 'Text' in k or 'Info' in k:
                            print(f"{k}: {v}")
                    
                    # Print raw keys to see valid ones
                    print(f"Keys: {list(data.keys())}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
