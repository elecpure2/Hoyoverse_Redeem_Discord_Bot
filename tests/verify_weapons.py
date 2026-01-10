import asyncio
import aiohttp
import sys
import re

# Force UTF-8 stdout
sys.stdout.reconfigure(encoding='utf-8')

# Mocking constants from upcoming.py
WEAPON_TYPE_KO = {
    'WEAPON_SWORD_ONE_HAND': '한손검', 'WEAPON_CLAYMORE': '양손검',
    'WEAPON_POLE': '장병기', 'WEAPON_BOW': '활', 'WEAPON_CATALYST': '법구',
    'Sword': '한손검', 'Claymore': '양손검', 'Polearm': '장병기',
    'Bow': '활', 'Catalyst': '법구',
    'Destruction': '파멸', 'Hunt': '순항', 'Erudition': '지식',
    'Harmony': '조화', 'Nihility': '허무', 'Preservation': '보존', 'Abundance': '풍요',
    'Attack': '타격', 'Stun': '강인', 'Anomaly': '이상', 'Support': '지원', 'Defense': '방어'
}

def clean_description(text):
    if not text: return ""
    text = re.sub(r'<[^>]+>', '', text)
    text = text.replace('\\n', ' ')
    return text[:50] + "..."

async def fetch_new_data_logic(game, session):
    print(f"\n--- Fetching New Data for {game} ---")
    game_url = {"gi": "gi", "hsr": "hsr", "zzz": "zzz"}[game]
    
    async with session.get(f"https://api.hakush.in/{game_url}/new.json") as resp:
        if resp.status != 200:
            print("Failed to fetch new.json")
            return []
        new_items = await resp.json()
    
    weapon_ids = []
    if game == 'gi': weapon_ids = new_items.get('weapon', [])
    elif game == 'hsr': weapon_ids = new_items.get('lightcone', [])
    elif game == 'zzz': weapon_ids = new_items.get('weapon', [])

    print(f"Found Weapon IDs: {weapon_ids}")
    
    results = []
    for wid in weapon_ids[:2]:
        endpoint = 'lightcone' if game == 'hsr' else 'weapon'
        lang = 'kr' if game == 'hsr' else 'ko'
        url = f"https://api.hakush.in/{game_url}/data/{lang}/{endpoint}/{wid}.json"
        
        async with session.get(url) as d_resp:
            if d_resp.status == 200:
                data = await d_resp.json()
                name = data.get('Name') or data.get('kr') or data.get('ItemName')
                
                # Type Extraction Logic
                type_str = "?"
                wtype = data.get('WeaponType') or data.get('BaseType')
                if isinstance(wtype, dict): # ZZZ
                    type_str = list(wtype.values())[0] if wtype else '?'
                elif wtype:
                    type_str = WEAPON_TYPE_KO.get(wtype, wtype)
                
                print(f"[{wid}] {name} ({type_str})")
                results.append((wid, name))
            else:
                print(f"Failed detail {wid}")
    return results

async def fetch_detail_logic(game, wid, session):
    print(f"\n--- Fetching Detail for {game} {wid} ---")
    game_url = {"gi": "gi", "hsr": "hsr", "zzz": "zzz"}[game]
    lang = 'kr' if game == 'hsr' else 'ko'
    endpoint = 'lightcone' if game == 'hsr' else 'weapon'
    url = f"https://api.hakush.in/{game_url}/data/{lang}/{endpoint}/{wid}.json"
    
    async with session.get(url) as resp:
        if resp.status == 200:
            data = await resp.json()
            
            # Desc
            desc = data.get('Desc') or data.get('Description')
            print(f"Desc: {clean_description(desc)}")
            
            # Skill / Refinement
            if game == 'hsr':
                skill = data.get('Refinements') or data.get('Skill')
                if isinstance(skill, dict):
                    ref1 = skill.get('1') or skill.get(1)
                    if ref1:
                        print(f"Skill: {ref1.get('Name')} - {clean_description(ref1.get('Desc', ''))}")
            elif game == 'zzz':
                talent = data.get('Talents')
                if isinstance(talent, dict):
                    ref1 = talent.get('1') or talent.get(1)
                    if ref1:
                         print(f"Skill: {ref1.get('Name')} - {clean_description(ref1.get('Desc', ''))}")
            elif game == 'gi':
                affix = data.get('Affix')
                if isinstance(affix, dict):
                    ref1 = affix.get('1')
                    if ref1:
                        print(f"Skill: {clean_description(ref1.get('Desc', ''))}")
        else:
            print("Failed fetch detail")

async def main():
    async with aiohttp.ClientSession() as session:
        for game in ['gi', 'hsr', 'zzz']:
            weapons = await fetch_new_data_logic(game, session)
            if weapons:
                await fetch_detail_logic(game, weapons[0][0], session)

if __name__ == "__main__":
    asyncio.run(main())
