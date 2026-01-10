import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import asyncio
from typing import Dict, List, Optional
import hakushin # Keep for Enums
from cogs.hoyo_shared import Game, GAME_COLORS, GAME_URLS, clean_description, HoyoSelectView, GameSelectView

class HoyoWeapons(commands.Cog):
    WEAPON_TYPE_KO = {
        'WEAPON_SWORD_ONE_HAND': '한손검', 'WEAPON_CLAYMORE': '양손검',
        'WEAPON_POLE': '장병기', 'WEAPON_BOW': '활', 'WEAPON_CATALYST': '법구',
        'Sword': '한손검', 'Claymore': '양손검', 'Polearm': '장병기',
        'Bow': '활', 'Catalyst': '법구',
        'Destruction': '파멸', 'Hunt': '수렵', 'Erudition': '지식',
        'Harmony': '조화', 'Nihility': '공허', 'Preservation': '보존', 'Abundance': '풍요',
        'Elation': '환락', 'Remembrance': '기억', 'General': '일반',
        'Attack': '타격', 'Stun': '강인', 'Anomaly': '이상', 'Support': '지원', 'Defense': '방어'
    }

    def __init__(self, bot):
        self.bot = bot
        self._weapon_cache_gi = {}
        self._weapon_cache_hsr = {}
        self._weapon_cache_zzz = {}

    def _get_weapon_term(self, game: Game) -> str:
        if game == Game.HSR: return "광추"
        return "무기"

    async def _load_all_weapon_caches(self):
        # GI
        if not self._weapon_cache_gi:
            try:
                # Raw API
                async with aiohttp.ClientSession() as session:
                    async with session.get("https://api.hakush.in/gi/data/weapon.json") as resp:
                         if resp.status == 200:
                             data = await resp.json()
                             if isinstance(data, dict):
                                 for k, v in data.items():
                                     name = v.get('KR') or v.get('kr') or v.get('Name')
                                     if name: self._weapon_cache_gi[name.lower()] = str(k)
                             elif isinstance(data, list):
                                 for item in data:
                                     name = item.get('KR') or item.get('kr') or item.get('Name')
                                     if name: self._weapon_cache_gi[name.lower()] = str(item.get('id'))
            except Exception as e:
                print(f"[원신] 무기 캐시 로드 실패: {e}")
        
        # HSR
        if not self._weapon_cache_hsr:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get("https://api.hakush.in/hsr/data/lightcone.json") as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            for k, v in data.items():
                                name = v.get('kr') or v.get('Name')
                                if name: self._weapon_cache_hsr[name.lower()] = str(k)
            except Exception as e:
                print(f"[스타레일] 광추 캐시 로드 실패: {e}")
        
        # ZZZ
        if not self._weapon_cache_zzz:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get("https://api.hakush.in/zzz/data/weapon.json") as resp:
                        if resp.status == 200:
                             data = await resp.json()
                             for k, v in data.items():
                                 raw_name = v.get('KO') or v.get('Info') or v.get('EN')
                                 if raw_name:
                                     clean_name = raw_name.replace("Item_Weapon_", "").replace("_Name", "").replace("_", " ")
                                     self._weapon_cache_zzz[clean_name.lower()] = str(k)
                                     self._weapon_cache_zzz[raw_name.lower()] = str(k)
            except Exception as e:
                print(f"[젠레스] 음동기 캐시 로드 실패: {e}")

    async def _search_weapon_all_games(self, name: str) -> list:
        await self._load_all_weapon_caches()
        name_lower = name.lower()
        results = []
        
        for weapon_name, weapon_id in self._weapon_cache_gi.items():
            if name_lower in weapon_name or weapon_name in name_lower:
                results.append({"game": Game.GI, "game_name": "원신", "name": weapon_name, "id": weapon_id})
                break
        
        for weapon_name, weapon_id in self._weapon_cache_hsr.items():
            if name_lower in weapon_name or weapon_name in name_lower:
                results.append({"game": Game.HSR, "game_name": "스타레일", "name": weapon_name, "id": weapon_id})
                break
        
        for weapon_name, weapon_id in self._weapon_cache_zzz.items():
            if name_lower in weapon_name or weapon_name in name_lower:
                results.append({"game": Game.ZZZ, "game_name": "젠레스 존 제로", "name": weapon_name, "id": weapon_id})
                break
        
        return results

    async def _show_weapon_detail_by_id(self, interaction, weapon_id, game: Game, game_name: str):
        weapon_term = self._get_weapon_term(game)
        color = GAME_COLORS.get(game, 0xFFD700)
        game_path = GAME_URLS.get(game, "gi")
        
        lang_path = "kr" if game == Game.HSR else "ko"
        endpoint = "lightcone" if game == Game.HSR else "weapon"
        
        url = f"https://api.hakush.in/{game_path}/data/{lang_path}/{endpoint}/{weapon_id}.json"
        
        async def send_msg(**kwargs):
            if interaction.response.is_done():
                await interaction.followup.send(**kwargs)
            else: # Should defer first usually
                await interaction.followup.send(**kwargs)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status != 200:
                        await send_msg(content=f"❌ {weapon_term} 상세 정보를 가져올 수 없어요.")
                        return
                    
                    data = await resp.json()
                    name = data.get('Name') or data.get('kr') or data.get('ItemName') or f"Unknown {weapon_id}"
                    
                    if game == Game.ZZZ and "Item_Weapon_" in name:
                         name = name.replace("Item_Weapon_", "").replace("_Name", "").replace("_", " ")
                    
                    raw_desc = data.get('Desc') or data.get('Description') or ''
                    desc = clean_description(raw_desc)
                    if not desc: desc = "설명 없음"
                    
                    rarity = data.get('Rarity') or data.get('Rank')
                    if isinstance(rarity, str):
                        import re
                        match = re.search(r'\d+', rarity)
                        rarity = int(match.group()) if match else 4
                    elif not isinstance(rarity, int):
                        rarity = 4
                    
                    stars = '⭐' * rarity
                    hakushin_url = f"https://{game_path}.hakush.in/{endpoint}/{weapon_id}"
                    
                    icon_url = ""
                    if game == Game.HSR:
                        icon_url = f"https://api.hakush.in/hsr/UI/lightcone/icon/{weapon_id}.webp"
                    elif game == Game.GI:
                        icon_name = data.get('Icon')
                        if icon_name: icon_url = f"https://api.hakush.in/gi/UI/{icon_name}.webp"
                    elif game == Game.ZZZ:
                         icon_name = data.get('Icon')
                         if icon_name: icon_url = f"https://api.hakush.in/zzz/UI/{icon_name}.webp"

                    embed = discord.Embed(
                        title=f"{stars} {name}",
                        description=f"{desc[:300]}\n\n[상세 정보 보기]({hakushin_url})",
                        color=color
                    )
                    if icon_url: embed.set_thumbnail(url=icon_url)
                    
                    # TYPE / PATH
                    if game == Game.HSR:
                        base_type = data.get('BaseType')
                        path_ko = self.WEAPON_TYPE_KO.get(base_type, base_type)
                        if path_ko: embed.add_field(name="🛤️ 운명의 길", value=path_ko, inline=True)
                    elif game == Game.GI:
                         wtype = data.get('WeaponType')
                         wtype_ko = self.WEAPON_TYPE_KO.get(wtype, wtype)
                         if wtype_ko: embed.add_field(name="⚔️ 종류", value=wtype_ko, inline=True)
                    elif game == Game.ZZZ:
                        wtype = data.get('WeaponType')
                        if isinstance(wtype, dict):
                             wtype_ko = list(wtype.values())[0]
                             embed.add_field(name="⚔️ 특성", value=wtype_ko, inline=True)
                    
                    # SKILL / PASSIVE (HSR FIX INCLUDED)
                    if game == Game.HSR:
                        skill = data.get('Refinements') or data.get('Skill')
                        if isinstance(skill, dict):
                            # New structure: Name/Desc at top, Level -> 1 -> ParamList
                            if 'Level' in skill:
                                rname = skill.get('Name') or '광추 스킬'
                                rdesc_tmpl = skill.get('Desc')
                                levels = skill.get('Level')
                                if levels and isinstance(levels, dict):
                                    l1 = levels.get('1') or levels.get(1)
                                    if l1:
                                         params = l1.get('ParamList', [])
                                         rdesc = clean_description(rdesc_tmpl, params)
                                         embed.add_field(name=f"🔮 {rname} (1중첩)", value=rdesc[:1024], inline=False)
                            else:
                                # Old structure: 1 -> Name/Desc
                                ref1 = skill.get('1') or skill.get(1)
                                if ref1:
                                    rname = ref1.get('Name', '광추 스킬')
                                    rdesc = clean_description(ref1.get('Desc', ''), ref1.get('Param', []))
                                    embed.add_field(name=f"🔮 {rname} (1중첩)", value=rdesc[:1024], inline=False)
                    
                    elif game == Game.ZZZ:
                         talent = data.get('Talents')
                         if isinstance(talent, dict):
                             ref1 = talent.get('1') or talent.get(1)
                             if ref1:
                                 rname = ref1.get('Name', '음동기 효과')
                                 rdesc = clean_description(ref1.get('Desc', ''), ref1.get('Param', []))
                                 embed.add_field(name=f"🔮 {rname} (1단계)", value=rdesc[:1024], inline=False)
                                 
                    elif game == Game.GI:
                        refinements = data.get('Refinement') or data.get('Refinements') or data.get('Affix')
                        if isinstance(refinements, dict):
                             # Try '1' or 1
                             ref1 = refinements.get('1') or refinements.get(1)
                             if ref1:
                                 rdesc = clean_description(ref1.get('Desc', ''))
                                 embed.add_field(name=f"🔮 무기 스킬 (1재련)", value=rdesc[:1024], inline=False)

                    embed.set_footer(text=f"데이터 출처: hakush.in | {game_name}")
                    await send_msg(embed=embed)

        except Exception as e:
            print(f"[무기상세] 오류: {e}")
            await send_msg(content=f"❌ 정보를 불러오는데 실패했어요: {e}")

    async def _show_new_weapons(self, interaction: discord.Interaction, game: Game, game_name: str):
         game_url = GAME_URLS.get(game, "gi")
         try:
             async with aiohttp.ClientSession() as session:
                 async with session.get(f"https://api.hakush.in/{game_url}/new.json") as resp:
                     if resp.status != 200:
                         await interaction.followup.send("❌ 신규 데이터를 가져올 수 없어요.")
                         return
                     new_items = await resp.json()
                 
                 weapon_ids = []
                 if game == Game.GI: weapon_ids = new_items.get('weapon', [])
                 elif game == Game.HSR: weapon_ids = new_items.get('lightcone', [])
                 elif game == Game.ZZZ: weapon_ids = new_items.get('weapon', [])
                 
                 if not weapon_ids:
                      await interaction.followup.send(f"❌ {game_name} 출시 예정 무기가 없어요.")
                      return

                 weapons = []
                 lang_path = "kr" if game == Game.HSR else "ko"
                 endpoint = "lightcone" if game == Game.HSR else "weapon"
                 
                 for wid in weapon_ids[:10]:
                      url = f"https://api.hakush.in/{game_url}/data/{lang_path}/{endpoint}/{wid}.json"
                      try:
                           async with session.get(url) as resp:
                                if resp.status == 200:
                                     d = await resp.json()
                                     from types import SimpleNamespace
                                     w = SimpleNamespace()
                                     w.id = wid
                                     w.name = d.get('Name') or d.get('kr') or d.get('ItemName') or f"{wid}"
                                     # ZZZ clean
                                     if game == Game.ZZZ:
                                         w.name = w.name.replace("Item_Weapon_", "").replace("_Name", "").replace("_", " ")
                                     
                                     r = d.get('Rarity') or d.get('Rank')
                                     if isinstance(r, str):
                                         import re
                                         match = re.search(r'\d+', r)
                                         w.rarity = int(match.group()) if match else 4
                                     else: w.rarity = r or 4
                                     
                                     w._type_str = "?"
                                     val = d.get('WeaponType') or d.get('BaseType')
                                     if isinstance(val, dict): w._type_str = list(val.values())[0] if val else '?'
                                     elif val: w._type_str = self.WEAPON_TYPE_KO.get(val, val)
                                     
                                     weapons.append(w)
                      except: pass
                 
                 color = GAME_COLORS.get(game, 0x87CEEB)
                 weapon_term = self._get_weapon_term(game)
                 
                 embed = discord.Embed(
                     title=f"⚔️ {game_name} 출시 예정 {weapon_term} (v{new_items.get('version', '?')})",
                     description=f"총 {len(weapon_ids)}개 - 번호를 눌러 상세 정보 확인",
                     color=color
                 )
                 
                 for i, weapon in enumerate(weapons):
                     stars = '⭐' * getattr(weapon, 'rarity', 4)
                     embed.add_field(
                         name=f"{i+1}. {stars} {weapon.name}",
                         value=f"종류: {weapon._type_str}",
                         inline=True
                     )
                 embed.set_footer(text=f"데이터 출처: hakush.in | {game_name}")
                 
                 view = HoyoSelectView(self, weapons, game, game_name, 'weapon')
                 msg = await interaction.followup.send(embed=embed, view=view)
                 view.message = msg
         except Exception as e:
             await interaction.followup.send(f"❌ 오류 발생: {e}")

    @app_commands.command(name="신무기", description="출시 예정 무기/광추를 확인해요")
    async def slash_new_weapon(self, interaction: discord.Interaction):
        embed = discord.Embed(title="🎮 게임 선택", description="출시 예정 무기를 확인할 게임을 선택하세요:", color=0x5865F2)
        view = GameSelectView(self, "weapon")
        await interaction.response.send_message(embed=embed, view=view)
        view.message = await interaction.original_response()

    @commands.command(name="신무기")
    async def new_weapon(self, ctx):
        embed = discord.Embed(title="🎮 게임 선택", description="출시 예정 무기를 확인할 게임을 선택하세요:", color=0x5865F2)
        view = GameSelectView(self, "weapon")
        view.message = await ctx.send(embed=embed, view=view)

    @app_commands.command(name="무기", description="무기/광추/음동기 상세 정보를 확인해요")
    @app_commands.describe(name="이름 (예: 회광, 밤인사, 스틸 쿠션)")
    async def slash_weapon(self, interaction: discord.Interaction, name: str):
        await interaction.response.defer()
        results = await self._search_weapon_all_games(name)
        if not results:
            await interaction.followup.send(f"❌ **{name}** 무기를 찾을 수 없어요.")
            return
        
        if len(results) == 1:
            r = results[0]
            await self._show_weapon_detail_by_id(interaction, r["id"], r["game"], r["game_name"])
        else:
            embed = discord.Embed(title=f"🎮 '{name}' - 게임 선택", description="여러 게임에서 무기를 찾았어요:", color=0x5865F2)
            for r in results: embed.add_field(name=r["game_name"], value=r["name"], inline=True)
            view = HoyoSelectView(self, results, results[0]["game"], results[0]["game_name"], 'weapon')
            msg = await interaction.followup.send(embed=embed, view=view)
            view.message = msg

    @commands.command(name="무기", aliases=["광추"])
    async def weapon(self, ctx, *, name: str = None):
        if not name:
            await ctx.send("❌ 이름을 입력해주세요.")
            return
        msg = await ctx.send(f"🔄 **{name}** 정보를 가져오는 중...")
        results = await self._search_weapon_all_games(name)
        if not results:
            await msg.edit(content=f"❌ **{name}** 무기를 찾을 수 없어요.")
            return
        
        if len(results) == 1:
            r = results[0]
            class FakeInteraction:
                def __init__(self, channel):
                     self.channel = channel
                     self.response = type('obj', (object,), {'is_done': lambda: True})
                     self.followup = self
                async def send(self, **kwargs):
                    if 'embed' in kwargs: await msg.edit(content=None, embed=kwargs['embed'])
                    elif 'content' in kwargs: await msg.edit(content=kwargs['content'])
            await self._show_weapon_detail_by_id(FakeInteraction(ctx.channel), r["id"], r["game"], r["game_name"])
        else:
            view = HoyoSelectView(self, results, results[0]["game"], results[0]["game_name"], 'weapon')
            await msg.edit(content=None, view=view)
            view.message = msg

async def setup(bot):
    await bot.add_cog(HoyoWeapons(bot))
