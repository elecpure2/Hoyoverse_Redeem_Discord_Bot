import asyncio
import aiohttp

async def main():
    print("Testing HSR Raw Character Detail Fetch...")
    # ID 1001 = March 7th
    url = "https://api.hakush.in/hsr/data/kr/character/1001.json"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                print(f"Status: {resp.status}")
                if resp.status == 200:
                    data = await resp.json()
                    print(f"Name: {data.get('Name')}")
                    print(f"Desc: {data.get('Desc')}")
                else:
                    print("Failed to fetch")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
