import aiohttp
import asyncio

async def check_url(url):
    print(f"Checking {url}...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, allow_redirects=True) as resp:
                print(f"Status: {resp.status}")
                print(f"Final URL: {resp.url}")
                if resp.history:
                    print("Redirection History:")
                    for r in resp.history:
                        print(f" - {r.url} ({r.status})")
    except Exception as e:
        print(f"Error: {e}")

async def main():
    await check_url("https://gi.hakush.in/")
    await check_url("https://hsr.hakush.in/")
    await check_url("https://zzz.hakush.in/")

if __name__ == "__main__":
    asyncio.run(main())
