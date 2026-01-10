import asyncio
import aiohttp
import sys

# Force UTF-8 stdout
sys.stdout.reconfigure(encoding='utf-8')

async def main():
    # ZZZ Weapon ID 14149 (from previous check)
    url = "https://api.hakush.in/zzz/data/ko/weapon/14149.json"
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as resp:
                print(f"Status: {resp.status}")
                if resp.status == 200:
                    data = await resp.json()
                    print(f"Keys: {list(data.keys())}")
                    # Check for type candidate fields
                    print(f"Profession: {data.get('Profession')}")
                    print(f"Type: {data.get('Type')}")
                    print(f"BaseType: {data.get('BaseType')}")
                    print(f"WeaponType: {data.get('WeaponType')}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
