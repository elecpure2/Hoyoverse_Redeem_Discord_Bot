import aiohttp
import asyncio

UID = "825112358"

async def test_enka():
    print(f"Fetching data for UID: {UID}...")
    async with aiohttp.ClientSession() as session:
        # 1. Get User Data to find Avatar IDs
        async with session.get(f"https://enka.network/api/uid/{UID}/", headers={"User-Agent": "HoyoRedeemBot/1.0"}) as resp:
            if resp.status != 200:
                print(f"Failed to fetch data: {resp.status}")
                return
            data = await resp.json()
            
        avatar_list = data.get("avatarInfoList", [])
        if not avatar_list:
            print("No avatars found.")
            return

        print(f"Found {len(avatar_list)} avatars.")
        first_avatar = avatar_list[0]
        avatar_id = first_avatar.get("avatarId")
        print(f"Testing Avatar ID: {avatar_id}")
        
        # Debug Skill Data
        print("\n--- SKILL DATA DEBUG ---")
        print(f"Skill Level Map: {first_avatar.get('skillLevelMap')}")
        print(f"Proud Skill Map: {first_avatar.get('proudSkillExtraLevelMap')}")
        print(f"Skill ID List:   {first_avatar.get('skillIdList')}")
        print("------------------------\n")

        # 2. Test Card URL Formats
        formats = [
            f"https://cards.enka.network/u/{UID}/{avatar_id}/image",
        ]

        for url in formats:
            try:
                async with session.get(url) as img_resp:
                    print(f"Testing URL: {url} -> Status: {img_resp.status}")
                    if img_resp.status == 200:
                        print(f"  > Content-Type: {img_resp.headers.get('Content-Type')}")
            except Exception as e:
                print(f"Error checking {url}: {e}")

if __name__ == "__main__":
    asyncio.run(test_enka())
