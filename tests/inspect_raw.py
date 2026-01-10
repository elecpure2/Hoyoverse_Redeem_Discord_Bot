import asyncio
import aiohttp
import json
import sys

# Force UTF-8 stdout
sys.stdout.reconfigure(encoding='utf-8')

async def main():
    urls = [
        ("HSR", "https://api.hakush.in/hsr/data/kr/lightcone/20023.json"),
        ("ZZZ", "https://api.hakush.in/zzz/data/ko/weapon/14149.json")
    ]
    
    async with aiohttp.ClientSession() as session:
        for game, url in urls:
            print(f"--- Checking {game} ---")
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    # Print raw Desc
                    print(f"Desc (Raw): '{data.get('Desc')}'")
                    # Print raw Name
                    print(f"Name (Raw): '{data.get('Name')}'")
                    # Check ZZZ other name keys?
                    if game == "ZZZ":
                         print(f"DisplayName: {data.get('DisplayName')}")
                         print(f"Title: {data.get('Title')}")
