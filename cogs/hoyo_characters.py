import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import asyncio
from typing import Dict, List, Optional
import hakushin # Keep for Enums if needed, or use shared
from cogs.hoyo_shared import Game, GAME_COLORS, GAME_URLS, clean_description, HoyoSelectView, GameSelectView

class HoyoCharacters(commands.Cog):
    ELEMENT_KO = {
        'Anemo': '바람', 'Pyro': '불', 'Hydro': '물', 'Electro': '번개',
        'Cryo': '얼음', 'Geo': '바위', 'Dendro': '풀', 'None': '무',
        'Wind': '바람', 'Fire': '불', 'Water': '물', 'Thunder': '번개', 'Lightning': '번개',
        'Ice': '얼음', 'Rock': '바위', 'Grass': '풀',
        'Physical': '물리', 'Quantum': '양자', 'Imaginary': '허수',
        'Electric': '전기', 'Ether': '에테르',
        'FireAttribute': '불', 'IceAttribute': '얼음', 'ElectricAttribute': '전기',
        'PhysicalAttribute': '물리', 'EtherAttribute': '에테르',
        'IceAttribute_Ghost': '얼음', 'FireAttribute_Ghost': '불'
    }

    HSR_STAT_NAMES = {
        'BreakDamageAddedRatioBase': '격파 특수효과',
        'StatusResistanceBase': '효과 저항',
        'SpeedDelta': '속도',
        'HPAddedRatio': 'HP%',
        'AttackAddedRatio': '공격력%',
        'DefenceAddedRatio': '방어력%',
        'CriticalChanceBase': '치명타 확률',
        'CriticalDamageBase': '치명타 피해',
        'StatusProbabilityBase': '효과 명중',
        'SPRatioBase': '에너지 회복 효율',
        'HealRatioBase': '치유량 보너스'
    }
    
    HSR_STAT_MAP = {
        'HPAddedRatio': 'HP %',
        'AttackAddedRatio': '공격력 %',
        'DefenceAddedRatio': '방어력 %',
        'CriticalChance': '치명타 확률',
        'CriticalDamage': '치명타 피해',
        'SpeedDelta': '속도',
        'BreakDamageAddedRatioBase': '격파 특수 효과',
        'SPRatioBase': '에너지 회복효율',
        'StatusProbabilityBase': '효과 명중',
        'StatusResistanceBase': '효과 저항',
        'PhysicalAddedRatio': '물리 피해', 
        'FireAddedRatio': '화염 피해',
        'IceAddedRatio': '얼음 피해',
        'ThunderAddedRatio': '번개 피해',
        'WindAddedRatio': '바람 피해',
        'QuantumAddedRatio': '양자 피해',
        'ImaginaryAddedRatio': '허수 피해',
        'HealRatioBase': '치유 보너스',
        'CriticalChanceBase': '치명타 확률',
        'CriticalDamageBase': '치명타 피해',
        'ElationDamageAddedRatioBase': '추가 공격 피해 증가',
    }

    def __init__(self, bot):
        self.bot = bot
        self._char_cache_gi = {}
        self._char_cache_hsr = {}
        self._char_cache_zzz = {}
        # Keep item caches here for HSR/ZZZ chars
        self._zzz_item_cache = {}
        self._hsr_item_cache = {}
        self._hsr_relic_cache = {}

    def _get_hsr_stat_text(self, key):
        return self.HSR_STAT_MAP.get(key, key)

    async def _load_zzz_item_cache(self):
        if self._zzz_item_cache: return
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("https://api.hakush.in/zzz/data/ko/item.json") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        for k, v in data.items():
                            name = v.get('Name') or v.get('kr') or v.get('ItemName')
                            if name:
                                self._zzz_item_cache[int(k)] = name
                        print(f"[ZZZ] 아이템 캐시 로드 완료: {len(self._zzz_item_cache)}개")
        except Exception as e:
            print(f"[ZZZ] 아이템 캐시 로드 실패: {e}")

    async def _load_hsr_item_cache(self):
        if self._hsr_item_cache: return
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("https://api.hakush.in/hsr/data/kr/item.json") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        for k, v in data.items():
                            try:
                                kid = int(k)
                                name = v.get('ItemName') or v.get('Name') or v.get('kr')
                                if name: self._hsr_item_cache[kid] = name
                            except: pass
                        print(f"[HSR] 아이템 캐시 로드 완료: {len(self._hsr_item_cache)}개")
        except Exception as e:
            print(f"[HSR] 아이템 캐시 로드 실패: {e}")

    async def _get_zzz_item_name(self, item_id: int) -> str:
        if not self._zzz_item_cache: await self._load_zzz_item_cache()
        return self._zzz_item_cache.get(item_id, f'소재 #{item_id}')

    async def _get_hsr_item_name(self, item_id: int) -> str:
        if not self._hsr_item_cache: await self._load_hsr_item_cache()
        return self._hsr_item_cache.get(item_id, f'소재 #{item_id}')

    async def _get_hsr_relic_name(self, relic_id):
        if relic_id in self._hsr_relic_cache:
            return self._hsr_relic_cache[relic_id]
        try:
             # Use raw API for reliability since hakushin might not have it cached or different endpoint
             # But here we stick to library or simple fetch?
             # Let's try raw fetch for name if HakushinAPI usage is discouraged
             # Or keep using HakushinAPI if it works for this specific call.
             # The existing code used HakushinAPI.
             # async with hakushin.HakushinAPI(Game.HSR, "kr") as client: ...
             # Let's use Raw API to be safe and remove dependency effectively.
             url = f"https://api.hakush.in/hsr/data/kr/relicset/{relic_id}.json"
             # Verify endpoint: relicset.json list or individual?
             # Usually data/kr/relicset.json is list.
             # data/kr/relicset/{id}.json is detail.
             async with aiohttp.ClientSession() as session:
                 async with session.get(url) as resp:
                     if resp.status == 200:
                         data = await resp.json()
                         name = data.get('Name') or data.get('kr')
                         if name:
                             self._hsr_relic_cache[relic_id] = name
                             return name
        except:
            pass
        return f"유물 {relic_id}"

    async def _load_all_char_caches(self):
        # GI
        if not self._char_cache_gi:
            try:
                # Raw API
                url = "https://api.hakush.in/gi/data/character.json" # List of chars
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as resp:
                         if resp.status == 200:
                             data = await resp.json()
                             # GI usually list of objects
                             if isinstance(data, list):
                                 for c in data:
                                     name = c.get('KR') or c.get('name') or c.get('Name')
                                     if name: self._char_cache_gi[name.lower()] = str(c.get('id'))
                             elif isinstance(data, dict):
                                 for k, v in data.items():
                                      name = v.get('KR') or v.get('name') or v.get('Name')
                                      if name: self._char_cache_gi[name.lower()] = str(k)
            except Exception as e:
                print(f"[원신] 캐릭터 캐시 로드 실패: {e}")

        # HSR
        if not self._char_cache_hsr:
            try:
                headers = {"User-Agent": "HoyoBot/1.0"}
                async with aiohttp.ClientSession() as session:
                    async with session.get("https://api.hakush.in/hsr/data/character.json", headers=headers) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            for char_id, char_data in data.items():
                                name = char_data.get('kr') or char_data.get('Name')
                                if name:
                                    self._char_cache_hsr[name.lower()] = str(char_id)
                            print(f"[스타레일] 캐릭터 캐시 로드 완료: {len(self._char_cache_hsr)}명")
            except Exception as e:
                print(f"[스타레일] 캐릭터 캐시 로드 실패: {e}")

        # ZZZ
        if not self._char_cache_zzz:
            try:
                # ZZZ Raw API
                url = "https://api.hakush.in/zzz/data/character.json"
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as resp:
                        if resp.status == 200:
                             data = await resp.json()
                             # ZZZ might be dict or list. Check?
                             # Usually dict.
                             if isinstance(data, dict):
                                 for k, v in data.items():
                                     # ZZZ: KO, kr, Name
                                     name = v.get('KO') or v.get('kr') or v.get('Name')
                                     if name: self._char_cache_zzz[name.lower()] = str(k)
                             elif isinstance(data, list):
                                 for c in data:
                                     name = c.get('KO') or c.get('kr') or c.get('Name')
                                     if name: self._char_cache_zzz[name.lower()] = str(c.get('id'))
            except Exception as e:
                print(f"[젠레스] 캐릭터 캐시 로드 실패: {e}")

    async def _search_character_all_games(self, name: str) -> list:
        await self._load_all_char_caches()
        name_lower = name.lower()
        results = []
        
        for char_name, char_id in self._char_cache_gi.items():
            if name_lower in char_name or char_name in name_lower:
                results.append({"game": Game.GI, "game_name": "원신", "name": char_name, "id": char_id})
                break
        
        for char_name, char_id in self._char_cache_hsr.items():
            if name_lower in char_name or char_name in name_lower:
                results.append({"game": Game.HSR, "game_name": "스타레일", "name": char_name, "id": char_id})
                break
        
        for char_name, char_id in self._char_cache_zzz.items():
            if name_lower in char_name or char_name in name_lower:
                results.append({"game": Game.ZZZ, "game_name": "젠레스 존 제로", "name": char_name, "id": char_id})
                break
        
        return results

    async def _fetch_raw_char_data(self, char_id: int, game: Game = Game.GI) -> dict:
        game_path = GAME_URLS.get(game, "gi")
        lang = "kr" if game == Game.HSR else "ko" # HSR uses kr
        url = f'https://api.hakush.in/{game_path}/data/{lang}/character/{char_id}.json'
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        return await resp.json()
        except:
            pass
        return {}

    def _create_dummy_hsr_char(self, raw, cid):
        from types import SimpleNamespace
        c = SimpleNamespace()
        c.id = cid
        c.name = raw.get('Name') or f"Unknown ({cid})"
        
        rarity_raw = raw.get('Rarity')
        if isinstance(rarity_raw, str):
            import re
            match = re.search(r'\d+', rarity_raw)
            c.rarity = int(match.group()) if match else 5
        else:
            c.rarity = rarity_raw or 5
            
        c.description = raw.get('Desc') or ''
        c.icon = f"https://api.hakush.in/hsr/UI/avatar/icon/{cid}.webp" 
        
        c.skills = {}
        if 'Skills' in raw:
            for sid, sdata in raw['Skills'].items():
                s = SimpleNamespace()
                s.name = sdata.get('Name') or f"Skill {sid}"
                s.description = sdata.get('Desc') or sdata.get('SimpleDesc') or ''
                s.type = sdata.get('Type')
                c.skills[sid] = s
        return c

    def _extract_hsr_stat_bonuses(self, raw_data: dict) -> dict:
        totals = {}
        skill_trees = raw_data.get('SkillTrees', {})
        for point_key, point_data in skill_trees.items():
             if isinstance(point_data, dict):
                 # Sometimes structure is deeper or iterating values?
                 # HSR SkillTree structure is complex.
                 # Let's iterate values if point_data is dict of levels
                 for level, info in point_data.items():
                      if isinstance(info, dict):
                           for s in info.get('StatusAddList', []):
                                stat_type = s.get('PropertyType', '')
                                value = s.get('Value', 0) or 0
                                if stat_type:
                                     totals[stat_type] = totals.get(stat_type, 0) + value
        return totals

    def _sum_materials(self, material_infos):
        # Helper for GI mats (library objects or raw?)
        # Assuming library objects or compatible Dicts.
        totals = {}
        for info in material_infos:
            for mat in info.materials: # If library object
                icon = getattr(mat, 'icon', None)
                key = (mat.name, mat.id, mat.rarity, icon)
                totals[key] = totals.get(key, 0) + mat.count
        return sorted(totals.items(), key=lambda x: (-x[0][2], x[0][0]))
    
    def _format_materials_compact(self, materials):
        lines = []
        for (name, mat_id, rarity, icon), count in materials:
            short_name = name.split()[-1] if len(name) > 10 else name
            lines.append(f"`{short_name}` x{count}")
        return ' | '.join(lines) if lines else '정보 없음'

    async def _send_character_info_by_id(self, send_func, char_id, game: Game, game_name: str):
        # We try to use Raw API fully if possible to detach from hakushin lib
        # But constructing Embeds from Raw JSON is tedious (need to replicate library logic).
        # We will use Raw API for HSR (due to library bugs) and Hakushin Lib for GI/ZZZ where stable?
        # User wants "Refactor and Fix". Raw API is safer for long term.
        # But replicating ALL fields (constellations, passives, ascensions) is huge work.
        # I will keep using Hakushin Lib for GI/ZZZ as they were working fine, mainly HSR broke.
        # And use Raw Fallback for HSR.
        
        detail = None
        raw_data = {}
        
        if game == Game.HSR:
            raw_data = await self._fetch_raw_char_data(char_id, game)
        elif game == Game.ZZZ:
            # ZZZ also unstable with lib, use Raw
            raw_data = await self._fetch_raw_char_data(char_id, game)
        
        try:
             # Needs hakushin.HakushinAPI
             async with hakushin.HakushinAPI(game, hakushin.Language.KO) as client:
                 detail = await client.fetch_character_detail(char_id)
        except Exception as e:
             if (game == Game.HSR or game == Game.ZZZ) and raw_data:
                 print(f"[Fallback] Raw used for {game_name} {char_id}")
                 # For ZZZ we might not have a dummy creator yet, but we will pass raw_data to builder
                 from types import SimpleNamespace
                 detail = SimpleNamespace()
                 detail.name = raw_data.get('Name') or raw_data.get('kr') or f"{char_id}"
                 detail.description = raw_data.get('Desc') or ''
                 detail.icon = f"https://api.hakush.in/zzz/UI/{raw_data.get('Icon')}.webp" if raw_data.get('Icon') else ""
                 detail.id = char_id
                 # Rarity?
                 r = raw_data.get('Rarity') or raw_data.get('Rank')
                 if isinstance(r, str):
                     import re
                     match = re.search(r'\d+', r)
                     detail.rarity = int(match.group()) if match else 5
                 else: detail.rarity = r or 5
             else:
                 await send_func(content=f"❌ 상세 정보를 가져올 수 없어요: {e}")
                 return

        if not detail and not raw_data: 
             await send_func(content="❌ 상세 정보를 가져올 수 없어요.")
             return

        rarity = getattr(detail, 'rarity', 5)
        stars = '⭐' * rarity if isinstance(rarity, int) else '⭐⭐⭐⭐⭐'
        color = GAME_COLORS.get(game, 0xFFD700)
        game_url = GAME_URLS.get(game, "gi")
        char_type = "character" if game != Game.ZZZ else "agent"
        hakushin_url = f"https://{game_url}.hakush.in/{char_type}/{char_id}"
        
        embeds = []
        if game == Game.GI:
            embeds = await self._build_gi_char_embeds(detail, color, hakushin_url, stars, char_id)
        elif game == Game.HSR:
            if not raw_data: raw_data = await self._fetch_raw_char_data(char_id, game)
            embeds = await self._build_hsr_char_embeds(detail, color, hakushin_url, stars, raw_data)
        elif game == Game.ZZZ:
            if not raw_data: raw_data = await self._fetch_raw_char_data(char_id, game) 
            embeds = await self._build_zzz_char_embeds(detail, color, hakushin_url, stars, game_name, raw_data)
            
        if embeds:
            await send_func(embeds=embeds)
        else:
            await send_func(content="❌ 정보를 불러올 수 없습니다.")

    async def _get_zzz_item_name(self, item_id):
        if not hasattr(self, '_zzz_item_cache') or not self._zzz_item_cache:
             self._zzz_item_cache = {}
             try:
                 async with aiohttp.ClientSession() as session:
                     async with session.get("https://api.hakush.in/zzz/data/ko/item.json") as resp:
                         if resp.status == 200:
                             data = await resp.json()
                             for k, v in data.items():
                                 if isinstance(v, dict):
                                     # ZZZ Item JSON uses lowercase 'name'
                                     self._zzz_item_cache[str(k)] = v.get('name') or v.get('Name')
                                 else: # ZZZ sometimes key->val string? Unlikely
                                     pass
             except Exception as e:
                 print(f"ZZZ Item Cache Error: {e}")
        
        return self._zzz_item_cache.get(str(item_id), f"#{item_id}")

    async def _get_gi_item_name(self, item_id):
        if not hasattr(self, '_gi_item_cache') or not self._gi_item_cache:
             self._gi_item_cache = {}
             try:
                 async with aiohttp.ClientSession() as session:
                     async with session.get("https://api.hakush.in/gi/data/kr/material.json") as resp:
                         if resp.status == 200:
                             data = await resp.json()
                             for k, v in data.items():
                                 if isinstance(v, dict):
                                     self._gi_item_cache[str(k)] = v.get('KR') or v.get('Name')
                     
                     # Also try item.json if material missed
                     async with session.get("https://api.hakush.in/gi/data/kr/item.json") as resp2:
                          if resp2.status == 200:
                              data2 = await resp2.json()
                              for k, v in data2.items():
                                 if str(k) not in self._gi_item_cache and isinstance(v, dict):
                                     self._gi_item_cache[str(k)] = v.get('KR') or v.get('Name')

             except Exception as e:
                 print(f"GI Item Cache Error: {e}")
        
        return self._gi_item_cache.get(str(item_id), f"#{item_id}")

    async def _build_gi_char_embeds(self, detail, color, hakushin_url, stars, char_id):
        embeds = []
        char_name = getattr(detail, 'name', '캐릭터')
        
        # 1. Basic Info
        desc_clean = clean_description(getattr(detail, 'description', ''))[:200]
        embed1 = discord.Embed(
            title=f"{stars} {char_name}",
            description=f"{desc_clean}\n\n[상세 정보 보기 (아이콘 포함)]({hakushin_url})",
            color=color
        )
        if hasattr(detail, 'icon') and detail.icon:
             embed1.set_thumbnail(url=detail.icon)

        # Materials (First)
        um = getattr(detail, 'upgrade_materials', None)
        if um:
            try:
                total_mats_dict = {}
                # Ascensions
                if hasattr(um, 'ascensions') and um.ascensions:
                    for info in um.ascensions:
                        if hasattr(info, 'materials'):
                            for mat in info.materials:
                                mname = getattr(mat, 'name', None)
                                if not mname and hasattr(mat, 'id'):
                                    mname = await self._get_gi_item_name(mat.id)
                                if mname:
                                    count = getattr(mat, 'count', 0)
                                    total_mats_dict[mname] = total_mats_dict.get(mname, 0) + count
                
                # Talents - structure: list[list[UpgradeMaterialInfo]]
                if hasattr(um, 'talents') and um.talents:
                    for talent_level_list in um.talents:
                        for info in talent_level_list:
                            if hasattr(info, 'materials'):
                                for mat in info.materials:
                                    mname = getattr(mat, 'name', None)
                                    if not mname and hasattr(mat, 'id'):
                                        mname = await self._get_gi_item_name(mat.id)
                                    if mname:
                                        count = getattr(mat, 'count', 0)
                                        total_mats_dict[mname] = total_mats_dict.get(mname, 0) + count
                
                if total_mats_dict:
                    sorted_mats = sorted(total_mats_dict.items(), key=lambda x: x[1], reverse=True)
                    m_lines = []
                    for name, count in sorted_mats:
                         if "Mora" in name or "모라" in name: continue 
                         m_lines.append(f"`{name}` x{count}")
                    
                    if m_lines:
                        chunk_size = 3
                        mat_chunks = [m_lines[i:i + chunk_size] for i in range(0, len(m_lines), chunk_size)]
                        mat_str = '\n'.join([' | '.join(chunk) for chunk in mat_chunks])
                        embed1.add_field(name="📦 육성 소재 (총합)", value=mat_str[:1024], inline=False)
                        
            except Exception as e: 
                import traceback
                print(f"[GI] Material error: {e}")
                traceback.print_exc()
        
        embeds.append(embed1)

        # 2. Skills
        skills = getattr(detail, 'skills', None)
        if skills:
            embed_skills = discord.Embed(title=f"⚔️ {char_name} - 전투 특성", color=color)
            for skill in skills:
                sname = getattr(skill, 'name', '?')
                sdesc = clean_description(getattr(skill, 'description', ''))
                if len(sdesc) > 400:
                    sdesc = sdesc[:397] + "..."
                embed_skills.add_field(name=f"🔹 {sname}", value=sdesc or "설명 없음", inline=False)
            embeds.append(embed_skills)

        # 3. Constellations
        consts = getattr(detail, 'constellations', None)
        if consts:
             embed_c = discord.Embed(title=f"✨ {char_name} - 운명의 자리", color=color)
             for i, c in enumerate(consts):
                 cname = getattr(c, 'name', f'{i+1}돌')
                 cdesc = clean_description(getattr(c, 'description', ''))
                 if len(cdesc) > 400:
                     cdesc = cdesc[:397] + "..."
                 embed_c.add_field(name=f"{i+1}. {cname}", value=cdesc, inline=False)
             embeds.append(embed_c)
             
        # 4. Character Illustration from Hakushin
        # GI uses name-based URLs like UI_Gacha_AvatarImg_Kachina.webp
        # Extract english name from icon field or use provided URL
        icon_field = getattr(detail, 'icon', '') or ''
        if icon_field:
            # Extract character name from icon URL (e.g., ".../UI_AvatarIcon_Kachina.webp" -> "Kachina")
            import re
            match = re.search(r'UI_AvatarIcon_(\w+)', icon_field)
            if match:
                char_eng_name = match.group(1)
                img_url = f"https://api.hakush.in/gi/UI/UI_Gacha_AvatarImg_{char_eng_name}.webp"
                embed_img = discord.Embed(title=f"🎨 {char_name} 일러스트", color=color)
                embed_img.set_image(url=img_url)
                embed_img.set_footer(text=f"데이터 출처: hakush.in | 원신")
                embeds.append(embed_img)
            else:
                embeds[-1].set_footer(text=f"데이터 출처: hakush.in | 원신")
        else:
            embeds[-1].set_footer(text=f"데이터 출처: hakush.in | 원신")
        
        return embeds

    async def _build_hsr_char_embeds(self, detail, color, hakushin_url, stars, raw_data):
         embeds = []
         
         # 1. Basic Info & Materials
         desc_clean = clean_description(getattr(detail, 'description', ''))[:200]
         embed1 = discord.Embed(
             title=f"{stars} {detail.name}",
             description=f"{desc_clean}\n\n[상세 정보 보기]({hakushin_url})",
             color=color
         )
         if hasattr(detail, 'icon') and detail.icon: embed1.set_thumbnail(url=detail.icon)

         # Materials
         total_mats = {}
         stats_data = raw_data.get('Stats', {})
         for key, stat_info in stats_data.items():
             for cost in stat_info.get('Cost', []):
                 iid, inum = cost.get('ItemID'), cost.get('ItemNum', 0)
                 if iid: total_mats[iid] = total_mats.get(iid, 0) + inum
         
         skill_trees = raw_data.get('SkillTrees', {})
         for point_data in skill_trees.values():
             if not isinstance(point_data, dict): continue
             def add_costs(cost_list):
                 for cost in cost_list:
                     iid, inum = cost.get('ItemID'), cost.get('ItemNum', 0)
                     if iid: total_mats[iid] = total_mats.get(iid, 0) + inum
             for key, info in point_data.items():
                 if isinstance(info, dict):
                     add_costs(info.get('MaterialList', []))
                     add_costs(info.get('LevelUpSkillCostList', []))

         if total_mats:
             m_lines = []
             sorted_mats = sorted(total_mats.items(), key=lambda x: x[1], reverse=True) # Sort by count desc
             for iid, count in sorted_mats:
                 if iid == 2: continue # Credits
                 iname = await self._get_hsr_item_name(iid)
                 m_lines.append(f"`{iname}` x{count}")
             
             # Format nicely
             if m_lines:
                 # Chunking 
                 chunk_size = 3
                 mat_chunks = [m_lines[i:i + chunk_size] for i in range(0, len(m_lines), chunk_size)]
                 mat_str = '\n'.join([' | '.join(chunk) for chunk in mat_chunks])
                 embed1.add_field(name="📦 육성 재료 (총합)", value=mat_str[:1024], inline=False)
         
         embeds.append(embed1)

         # 2. Skills (Clean numeric params)
         embed_skills = discord.Embed(title=f"⚔️ {detail.name} - 전투 스킬", color=color)
         skills_raw = raw_data.get('Skills', {})
         # Sort by simplified execution order usually? Basic -> Skill -> Ult -> Talent -> Maze
         # Keys are IDs. 
         # We try to find relevant skills. 
         seen_skills = set()
         for sid, sdata in skills_raw.items():
             name = sdata.get('Name')
             if not name or name in seen_skills: continue
             seen_skills.add(name)
             
             # Get Level 1 or max? User wants info.
             # Raw data 'Skills' dictionary usually has 'Level' -> {1: ...} ?
             # Let's check a raw dump structure?
             # Usually 'Skills' -> ID -> { Name, Desc, Level: {1: { ... ParamList ... }} }
             # Or just 'Skills' -> ID -> { Name, Desc, ParamList } (if flat)
             # Looking at upcoming.py, it seemed HSR structure varies.
             # Assuming standard structure:
             desc_tmpl = sdata.get('Desc', '')
             params = []
             
             # Try Level 1
             if 'Level' in sdata and '1' in sdata['Level']:
                 params = sdata['Level']['1'].get('ParamList', [])
             elif 'ParamList' in sdata:
                 params = sdata['ParamList']
             
             # Clean
             desc = clean_description(desc_tmpl, params)
             embed_skills.add_field(name=f"🔹 {name}", value=desc[:1024], inline=False)
             
         embeds.append(embed_skills)

         # 3. Eidolons (Ranks)
         ranks_raw = raw_data.get('Ranks', {})
         if ranks_raw:
             embed_ranks = discord.Embed(title=f"✨ {detail.name} - 성혼", color=color)
             for rid, rdata in ranks_raw.items():
                 name = rdata.get('Name')
                 desc_tmpl = rdata.get('Desc', '')
                 params = rdata.get('Param', []) or rdata.get('ParamList', [])
                 desc = clean_description(desc_tmpl, params)
                 embed_ranks.add_field(name=f"{rid}. {name}", value=desc[:1024], inline=False)
             embeds.append(embed_ranks)

         embeds[-1].set_footer(text="데이터 출처: hakush.in | 스타레일")

         # 4. Character Illustration (gacha_art)
         img_url = getattr(detail, 'gacha_art', None)
         # Fallback: construct URL using character ID if library doesn't provide gacha_art
         if not img_url:
             char_id = getattr(detail, 'id', None)
             if char_id:
                 img_url = f"https://api.hakush.in/hsr/UI/avatardrawcard/{char_id}.webp"
         
         if img_url:
             embed_img = discord.Embed(title=f"🎨 {detail.name} 일러스트", color=color)
             embed_img.set_image(url=img_url)
             embed_img.set_footer(text="데이터 출처: hakush.in | 스타레일")
             embeds.append(embed_img)
         
         return embeds
    
    async def _build_zzz_char_embeds(self, detail, color, hakushin_url, stars, game_name, raw_data):
        try:
            embeds = []
            char_id = getattr(detail, 'id', None) or raw_data.get('Id')
            char_name = getattr(detail, 'name', None) or raw_data.get('Name') or f'캐릭터 {char_id}'
            
            # 1. Basic Info
            desc_clean = clean_description(getattr(detail, 'description', '') or raw_data.get('Desc', ''))[:200]
            embed1 = discord.Embed(
                title=f"{stars} {char_name}",
                description=f"{desc_clean}\n\n[상세 정보 보기 (아이콘 포함)]({hakushin_url})",
                color=color
            )
            
            # Thumbnail
            icon = getattr(detail, 'icon', None)
            if not icon and raw_data.get('Icon'):
                icon = f"https://api.hakush.in/zzz/UI/{raw_data.get('Icon')}.webp"
            if icon:
                embed1.set_thumbnail(url=icon)
            
            # Element & Faction info from library
            element = getattr(detail, 'element', None)
            faction = getattr(detail, 'faction', None)
            if element or faction:
                element_name = getattr(element, 'name', str(element)) if element else ''
                faction_name = getattr(faction, 'name', str(faction)) if faction else ''
                element_ko = self.ELEMENT_KO.get(element_name, element_name) if element_name else ''
                embed1.add_field(name="정보", value=f"**속성**: {element_ko}\n**소속**: {faction_name}", inline=False)
            
            # === Materials from Level (raw_data) ===
            level_data = raw_data.get('Level', {})
            total_mats = {}
            for level_key, level_info in level_data.items():
                if isinstance(level_info, dict):
                    materials = level_info.get('Materials', {})
                    if isinstance(materials, dict):
                        for mat_id, mat_count in materials.items():
                            mid = int(mat_id)
                            total_mats[mid] = total_mats.get(mid, 0) + mat_count
            
            if total_mats:
                m_lines = []
                sorted_mats = sorted(total_mats.items(), key=lambda x: x[1], reverse=True)
                for mid, count in sorted_mats:
                    if mid == 10:  # Dennies (currency)
                        continue
                    mname = await self._get_zzz_item_name(mid)
                    m_lines.append(f"`{mname}` x{count}")
                
                if m_lines:
                    chunk_size = 3
                    mat_chunks = [m_lines[i:i + chunk_size] for i in range(0, len(m_lines), chunk_size)]
                    mat_str = '\n'.join([' | '.join(chunk) for chunk in mat_chunks])
                    embed1.add_field(name="📦 육성 재료 (총합)", value=mat_str[:1024], inline=False)
            
            embeds.append(embed1)

            # === 2. Skills from hakushin library (detail.skills) ===
            lib_skills = getattr(detail, 'skills', None)
            if lib_skills and isinstance(lib_skills, dict):
                embed_skills = discord.Embed(title=f"⚔️ {char_name} - 스킬", color=color)
                
                for skill_type, skill_obj in lib_skills.items():
                    if not skill_obj:
                        continue
                    # skill_obj.descriptions is a list of CharacterSkillDesc
                    descs = getattr(skill_obj, 'descriptions', [])
                    for skill_desc in descs:
                        sname = getattr(skill_desc, 'name', skill_type)
                        sdesc = getattr(skill_desc, 'description', '')
                        params = getattr(skill_desc, 'params', None)
                        
                        sdesc = clean_description(sdesc, params)
                        if sdesc:
                            if len(sdesc) > 400:
                                sdesc = sdesc[:397] + "..."
                            embed_skills.add_field(name=f"🔹 {sname}", value=sdesc, inline=False)
                
                if len(embed_skills.fields) > 0:
                    embeds.append(embed_skills)

            # === 3. Mindscape Cinema from raw_data.Talent ===
            # Library potentials is empty, so use raw API data
            talent_data = raw_data.get('Talent', {})
            if talent_data and isinstance(talent_data, dict):
                embed_cinema = discord.Embed(title=f"✨ {char_name} - 마인드스케이프 시네마", color=color)
                
                sorted_keys = sorted(talent_data.keys(), key=lambda x: int(x) if str(x).isdigit() else 99)
                
                for k in sorted_keys:
                    t = talent_data[k]
                    if not isinstance(t, dict):
                        continue
                    tname = t.get('Name') or f'{k}단계'
                    tdesc = t.get('Desc', '')
                    params = t.get('Param', []) or t.get('Params', [])
                    tdesc = clean_description(tdesc, params)
                    
                    if tdesc:
                        if len(tdesc) > 500:
                            tdesc = tdesc[:497] + "..."
                        embed_cinema.add_field(name=f"{k}. {tname}", value=tdesc, inline=False)
                
                if len(embed_cinema.fields) > 0:
                    embeds.append(embed_cinema)
            
            # === 4. Character Illustration (phase_3_cinema_art) ===
            img_url = getattr(detail, 'phase_3_cinema_art', None)
            if not img_url:
                # Fallback to Icon
                icon_field = raw_data.get('Icon', '')
                if icon_field:
                    img_url = f"https://api.hakush.in/zzz/UI/{icon_field}.webp"
            
            if img_url:
                embed_img = discord.Embed(title=f"🎨 {char_name} 일러스트", color=color)
                embed_img.set_image(url=img_url)
                embed_img.set_footer(text=f"데이터 출처: hakush.in | {game_name}")
                embeds.append(embed_img)
            else:
                if embeds:
                    embeds[-1].set_footer(text=f"데이터 출처: hakush.in | {game_name}")
            
            return embeds
        except Exception as e:
            import traceback
            print(f"[ZZZ] Build embeds error: {e}")
            traceback.print_exc()
            error_embed = discord.Embed(title="❌ 오류 발생", description=f"캐릭터 정보 로드 중 오류: {e}", color=0xFF0000)
            return [error_embed]

    async def _show_character_detail_by_id(self, interaction, char_id, game: Game, game_name: str):
        async def send_func(content=None, embed=None, embeds=None):
            if interaction.response.is_done():
                 sender = interaction.followup.send
            else:
                 sender = interaction.response.send_message # But wait, usually we deferred?
                 # If deferred, use follow up.
                 # The caller usually defers.
                 sender = interaction.followup.send
                 
            if embeds:
                for i in range(0, len(embeds), 10):
                    await sender(embeds=embeds[i:i+10])
            elif embed:
                await sender(embed=embed)
            elif content:
                await sender(content=content)
        
        await self._send_character_info_by_id(send_func, char_id, game, game_name)

    async def _show_new_characters(self, interaction: discord.Interaction, game: Game, game_name: str):
         # Fetch new.json
         game_url = GAME_URLS.get(game, "gi")
         try:
             async with aiohttp.ClientSession() as session:
                 async with session.get(f"https://api.hakush.in/{game_url}/new.json") as resp:
                     if resp.status != 200:
                         await interaction.followup.send("❌ 신규 데이터를 가져올 수 없어요.")
                         return
                     new_items = await resp.json()
                     
                 # Get char IDs
                 char_ids = new_items.get('character', []) or new_items.get('agent', [])
                 if not char_ids:
                      await interaction.followup.send(f"❌ {game_name} 출시 예정 캐릭터가 없어요.")
                      return
                      
                 # Fetch details
                 chars = []
                 for cid in char_ids[:10]:
                      # Fetch minimal info using existing raw fetcher
                      raw = await self._fetch_raw_char_data(cid, game)
                      if raw:
                           # Wrap in object or dict
                           from types import SimpleNamespace
                           c = SimpleNamespace()
                           c.id = cid
                           c.name = raw.get('Name') or raw.get('kr') or raw.get('ItemName') or f"{cid}"
                           # ZZZ name clean
                           if game == Game.ZZZ:
                                if '_' in c.name: c.name = c.name.split('_')[-1]
                           
                           r = raw.get('Rarity') or raw.get('Rank')
                           if isinstance(r, str):
                               import re
                               match = re.search(r'\d+', r)
                               c.rarity = int(match.group()) if match else 5
                           else: c.rarity = r or 5
                           chars.append(c)
                 
                 color = GAME_COLORS.get(game, 0xFFD700)
                 char_lines = []
                 for i, c in enumerate(chars):
                      star = getattr(c, 'rarity', 5)
                      char_lines.append(f"**{i+1}. {c.name}** (⭐{star})")
                 
                 # Join characters with spaces for inline display (3 per line)
                 lines = []
                 for i in range(0, len(char_lines), 3):
                     lines.append("  ".join(char_lines[i:i+3]))
                 char_text = "\n".join(lines)
                 
                 embed = discord.Embed(
                     title=f"🌟 {game_name} 출시 예정 캐릭터 (v{new_items.get('version', '?')})",
                     description=f"총 {len(char_ids)}명 - 번호를 눌러 상세 정보 확인\n\n{char_text}",
                     color=color
                 )
                 embed.set_footer(text=f"데이터 출처: hakush.in | {game_name}")
                 
                 view = HoyoSelectView(self, chars, game, game_name, 'character')
                 msg = await interaction.followup.send(embed=embed, view=view)
                 view.message = msg
         except Exception as e:
             print(f"Error showing new chars: {e}")
             await interaction.followup.send(f"❌ 오류 발생: {e}")

    @app_commands.command(name="신캐", description="출시 예정 캐릭터를 확인해요 (원신/스타레일/젠레스)")
    async def slash_new_char(self, interaction: discord.Interaction):
        embed = discord.Embed(title="🎮 게임 선택", description="출시 예정 캐릭터를 확인할 게임을 선택하세요:", color=0x5865F2)
        view = GameSelectView(self, "character")
        await interaction.response.send_message(embed=embed, view=view)
        view.message = await interaction.original_response()

    @commands.command(name="신캐")
    async def new_char(self, ctx):
        embed = discord.Embed(title="🎮 게임 선택", description="출시 예정 캐릭터를 확인할 게임을 선택하세요:", color=0x5865F2)
        view = GameSelectView(self, "character")
        view.message = await ctx.send(embed=embed, view=view)

    @app_commands.command(name="캐릭터", description="캐릭터 상세 정보를 확인해요 (원신/스타레일/젠레스)")
    @app_commands.describe(char_name="캐릭터 이름 (예: 느비예트, 아케론, 엘렌)")
    async def slash_character(self, interaction: discord.Interaction, char_name: str):
        await interaction.response.defer()
        results = await self._search_character_all_games(char_name)
        if not results:
            await interaction.followup.send(f"❌ **{char_name}** 캐릭터를 찾을 수 없어요.")
            return
        
        if len(results) == 1:
            result = results[0]
            await self._show_character_detail_by_id(interaction, result["id"], result["game"], result["game_name"])
        else:
            embed = discord.Embed(title=f"🎮 '{char_name}' - 게임 선택", description="여러 게임에서 캐릭터를 찾았어요:", color=0x5865F2)
            for r in results: embed.add_field(name=r["game_name"], value=r["name"], inline=True)
            view = HoyoSelectView(self, results, results[0]["game"], results[0]["game_name"], 'character')
            msg = await interaction.followup.send(embed=embed, view=view)
            view.message = msg

    @commands.command(name="캐릭터")
    async def character(self, ctx, *, name: str = None):
        if not name:
            await ctx.send("❌ 캐릭터 이름을 입력해주세요.")
            return
        msg = await ctx.send(f"🔄 **{name}** 정보를 가져오는 중...")
        results = await self._search_character_all_games(name)
        if not results:
            await msg.edit(content=f"❌ **{name}** 캐릭터를 찾을 수 없어요.")
            return
        
        if len(results) == 1:
            r = results[0]
            class FakeInteraction:
                def __init__(self, channel):
                     self.channel = channel
                     self.response = type('obj', (object,), {'is_done': lambda: True})
                     self.followup = self
                async def send(self, **kwargs):
                    if 'embeds' in kwargs: 
                        await msg.edit(content=None, embed=kwargs['embeds'][0])
                        for e in kwargs['embeds'][1:]: await ctx.send(embed=e)
                    elif 'embed' in kwargs: await msg.edit(content=None, embed=kwargs['embed'])
                    elif 'content' in kwargs: await msg.edit(content=kwargs['content'])
            
            await self._show_character_detail_by_id(FakeInteraction(ctx.channel), r["id"], r["game"], r["game_name"])
        else:
            view = HoyoSelectView(self, results, results[0]["game"], results[0]["game_name"], 'character')
            await msg.edit(content=None, view=view)
            view.message = msg

async def setup(bot):
    await bot.add_cog(HoyoCharacters(bot))
