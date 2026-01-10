
import aiohttp
import asyncio
import json

async def debug_zzz_detail():
    char_id = 1251 # Miyabi
    url = f"https://api.hakush.in/zzz/data/ko/character/{char_id}.json"
    
    async with aiohttp.ClientSession() as session:
        print(f"Fetching ZZZ character {char_id}...")
        async with session.get(url) as resp:
            if resp.status != 200:
                print(f"Failed: {resp.status}")
                return
                
            data = await resp.json()
            # print keys
            print(f"Keys: {data.keys()}")
            
            # Inspect Skills
            skills = data.get('Skill', {})
            if not skills: skills = data.get('SkillList', {})
            
            print(f"\nSkills Type: {type(skills)}")
            if isinstance(skills, dict) and skills:
                 k = list(skills.keys())[0]
                 print(f"First Skill [{k}]: {skills[k]}")
            elif isinstance(skills, list) and skills:
                 print(f"First Skill: {skills[0]}")
            
            # Inspect Talents (Mindscape)
            talents = data.get('Talent', {}) 
            if not talents: talents = data.get('Potential', {})
            
            print(f"\nTalents/Ranks: {type(talents)}")
            if isinstance(talents, dict):
                for k, v in talents.items():
                    print(f"Rank {k} keys: {v.keys()}")
                    # Check for Cinema 3 image url logic?
                    if str(k) == '3' or k == 3:
                        print(f"Rank 3 Data: {v}")
            
            # Inspect Images/Icon references in Rank 3
            # Check for specific "Cinema" art logic?

if __name__ == "__main__":
    asyncio.run(debug_zzz_detail())
