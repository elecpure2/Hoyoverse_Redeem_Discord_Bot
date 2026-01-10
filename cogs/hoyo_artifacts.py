import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import asyncio
from typing import Dict, List, Optional
import hakushin # Keep for Enums
from cogs.hoyo_shared import Game, GAME_COLORS, GAME_URLS, clean_description, HoyoSelectView, GameSelectView

class HoyoArtifacts(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._artifact_cache_gi = {}
        self._artifact_cache_hsr = {}
        self._artifact_cache_zzz = {}
        self._hsr_relic_cache = {} # Name cache for detailed lookup? Or just stick to raw artifact cache.

    def _get_artifact_term(self, game: Game) -> str:
        if game == Game.HSR: return "유물/장신구"
        if game == Game.ZZZ: return "디스크"
        return "성유물"

    def _format_hsr_desc(self, desc: str, params: list) -> str:
        """스타레일 설명의 placeholder를 실제 값으로 치환"""
        import re
        if not desc:
            return ""
        
        # Remove HTML-like tags
        desc = re.sub(r'<[^>]+>', '', desc)
        
        # Replace placeholders like #1[i]%, #2[f1]% etc
        def replace_placeholder(match):
            idx = int(match.group(1)) - 1
            fmt = match.group(2)  # 'i', 'f1', 'f2' etc
            suffix = match.group(3) or ''  # '%' or empty
            
            if idx < len(params):
                val = params[idx]
                if suffix == '%':
                    val = val * 100
                if fmt == 'i':
                    return f"{int(val)}{suffix}"
                elif fmt.startswith('f'):
                    decimals = int(fmt[1]) if len(fmt) > 1 else 1
                    return f"{val:.{decimals}f}{suffix}"
                else:
                    return f"{val}{suffix}"
            return match.group(0)
        
        desc = re.sub(r'#(\d+)\[([^\]]+)\](%?)', replace_placeholder, desc)
        return desc

    async def _load_all_artifact_caches(self):
        # GI - structure: { "15003": { "set": { "2150030": { "name": { "KR": "..." } } } } }
        if not self._artifact_cache_gi:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get("https://api.hakush.in/gi/data/artifact.json") as resp:
                         if resp.status == 200:
                             data = await resp.json()
                             for art_id, art_data in data.items():
                                 if isinstance(art_data, dict):
                                     set_data = art_data.get('set', {})
                                     if set_data:
                                         # Get first set entry for the name
                                         first_set = next(iter(set_data.values()), {})
                                         name_data = first_set.get('name', {})
                                         name = name_data.get('KR') or name_data.get('EN')
                                         if name:
                                             self._artifact_cache_gi[name.lower()] = str(art_id)
            except Exception as e:
                print(f"[원신] 성유물 캐시 로드 실패: {e}")

        # HSR - structure: { "101": { "kr": "흔적을 남기지 않은 과객", "set": {...} } }
        if not self._artifact_cache_hsr:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get("https://api.hakush.in/hsr/data/relicset.json") as resp:
                         if resp.status == 200:
                             data = await resp.json()
                             for art_id, art_data in data.items():
                                 if isinstance(art_data, dict):
                                     name = art_data.get('kr') or art_data.get('en')
                                     if name:
                                         self._artifact_cache_hsr[name.lower()] = str(art_id)
            except Exception as e:
                print(f"[스타레일] 유물 캐시 로드 실패: {e}")

        # ZZZ - structure: { "31000": { "KO": { "name": "...", "desc2": "...", "desc4": "..." } } }
        if not self._artifact_cache_zzz:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get("https://api.hakush.in/zzz/data/equipment.json") as resp:
                        if resp.status == 200:
                             data = await resp.json()
                             for art_id, art_data in data.items():
                                 if isinstance(art_data, dict):
                                     ko_data = art_data.get('KO', {})
                                     name = ko_data.get('name') if isinstance(ko_data, dict) else None
                                     if name:
                                         self._artifact_cache_zzz[name.lower()] = str(art_id)
            except Exception as e:
                print(f"[젠레스] 디스크 캐시 로드 실패: {e}")

    async def _search_artifact_all_games(self, name: str) -> list:
        await self._load_all_artifact_caches()
        name_lower = name.lower()
        results = []
        
        for art_name, art_id in self._artifact_cache_gi.items():
            if name_lower in art_name or art_name in name_lower:
                results.append({"game": Game.GI, "game_name": "원신", "name": art_name, "id": art_id})
                break 
        
        for art_name, art_id in self._artifact_cache_hsr.items():
            if name_lower in art_name or art_name in name_lower:
                 results.append({"game": Game.HSR, "game_name": "스타레일", "name": art_name, "id": art_id})
                 break
        
        for art_name, art_id in self._artifact_cache_zzz.items():
            if name_lower in art_name or art_name in name_lower:
                 results.append({"game": Game.ZZZ, "game_name": "젠레스 존 제로", "name": art_name, "id": art_id})
                 break
                 
        return results

    async def _show_artifact_detail_by_id(self, interaction, artifact_id, game: Game, game_name: str, artifact_name: str = None):
        """성유물/유물/디스크 상세 정보를 표시합니다."""
        artifact_term = self._get_artifact_term(game)
        color = GAME_COLORS.get(game, 0x9370DB)
        
        try:
            game_path = GAME_URLS.get(game, "gi")
            
            # Use list API to get set effects (more reliable structure)
            if game == Game.GI:
                api_url = "https://api.hakush.in/gi/data/artifact.json"
                hakushin_endpoint = "artifact"
            elif game == Game.HSR:
                api_url = "https://api.hakush.in/hsr/data/relicset.json"
                hakushin_endpoint = "relicset"
            else:  # ZZZ
                api_url = "https://api.hakush.in/zzz/data/equipment.json"
                hakushin_endpoint = "equipment"
            
            async def send_msg(**kwargs):
                if interaction.response.is_done():
                     await interaction.followup.send(**kwargs)
                else:
                     await interaction.followup.send(**kwargs)

            async with aiohttp.ClientSession() as session:
                 async with session.get(api_url) as resp:
                     if resp.status != 200:
                         await send_msg(content=f"❌ {artifact_term} 정보를 가져올 수 없어요.")
                         return
                     
                     all_data = await resp.json()
                     art_data = all_data.get(str(artifact_id))
                     
                     if not art_data:
                         await send_msg(content=f"❌ {artifact_term}을 찾을 수 없어요.")
                         return
                     
                     # Extract name and set effects based on game
                     name = artifact_name
                     set_2pc = None
                     set_4pc = None
                     icon_url = ""
                     
                     if game == Game.GI:
                         # GI: { "set": { "id": { "name": {"KR": "...", ...}, "desc": {"KR": "..."} } } }
                         set_data = art_data.get('set', {})
                         set_items = list(set_data.values())
                         if len(set_items) >= 1:
                             first_set = set_items[0]
                             if not name:
                                 name = first_set.get('name', {}).get('KR') or first_set.get('name', {}).get('EN')
                             set_2pc = first_set.get('desc', {}).get('KR') or first_set.get('desc', {}).get('EN')
                         if len(set_items) >= 2:
                             set_4pc = set_items[1].get('desc', {}).get('KR') or set_items[1].get('desc', {}).get('EN')
                         
                         icon_name = art_data.get('icon')
                         if icon_name:
                             icon_url = f"https://api.hakush.in/gi/UI/{icon_name}.webp"
                     
                     elif game == Game.HSR:
                         # HSR: { "kr": "...", "set": { "2": { "kr":"...", "ParamList":[...] }, "4": {...} } }
                         if not name:
                             name = art_data.get('kr') or art_data.get('en')
                         
                         set_data = art_data.get('set', {})
                         if '2' in set_data:
                             desc = set_data['2'].get('kr') or set_data['2'].get('en', '')
                             params = set_data['2'].get('ParamList', [])
                             set_2pc = self._format_hsr_desc(desc, params)
                         if '4' in set_data:
                             desc = set_data['4'].get('kr') or set_data['4'].get('en', '')
                             params = set_data['4'].get('ParamList', [])
                             set_4pc = self._format_hsr_desc(desc, params)
                         
                         icon_name = art_data.get('icon')
                         if icon_name:
                             icon_url = f"https://api.hakush.in/hsr/UI/{icon_name}"
                     
                     elif game == Game.ZZZ:
                         # ZZZ: { "KO": { "name": "...", "desc2": "...", "desc4": "..." } }
                         ko_data = art_data.get('KO', {})
                         if not name and isinstance(ko_data, dict):
                             name = ko_data.get('name')
                         
                         if isinstance(ko_data, dict):
                             set_2pc = ko_data.get('desc2', '')
                             set_4pc = ko_data.get('desc4', '')
                         
                         # Clean ZZZ color tags
                         if set_2pc:
                             set_2pc = clean_description(set_2pc)
                         if set_4pc:
                             set_4pc = clean_description(set_4pc)
                         
                         icon_name = art_data.get('icon')
                         if icon_name:
                             icon_url = f"https://api.hakush.in/zzz/{icon_name}"
                     
                     if not name:
                         name = f"세트 #{artifact_id}"
                     else:
                         # Capitalize first letter of name if it's lowercase
                         name = name.title() if name.islower() else name
                     
                     hakushin_url = f"https://{game_path}.hakush.in/{hakushin_endpoint}/{artifact_id}"
                     
                     # Build description
                     desc_parts = [f"[상세 정보 보기]({hakushin_url})"]
                     
                     if set_2pc or set_4pc:
                         desc_parts.append("")  # Empty line
                         if set_2pc:
                             desc_parts.append(f"**2세트 효과**\n{set_2pc}")
                         if set_4pc:
                             desc_parts.append(f"\n**4세트 효과**\n{set_4pc}")
                     
                     embed = discord.Embed(
                         title=f"🏺 {name}",
                         description="\n".join(desc_parts),
                         color=color
                     )
                     if icon_url: 
                         embed.set_thumbnail(url=icon_url)
                     
                     embed.set_footer(text=f"데이터 출처: hakush.in | {game_name}")
                     await send_msg(embed=embed)
                     
        except Exception as e:
            print(f"[성유물] 오류: {e}")
            import traceback
            traceback.print_exc()
            await send_msg(content=f"❌ 정보를 불러오는데 실패했어요: {e}")

    async def _show_new_artifacts(self, interaction: discord.Interaction, game: Game, game_name: str):
        game_url = GAME_URLS.get(game, "gi")
        try:
            async with aiohttp.ClientSession() as session:
                # Fetch new.json to get new artifact IDs
                async with session.get(f"https://api.hakush.in/{game_url}/new.json") as resp:
                    if resp.status != 200:
                        await interaction.followup.send("❌ 신규 데이터를 가져올 수 없어요.")
                        return
                    new_items = await resp.json()
                
                artifact_ids = []
                if game == Game.GI: 
                    artifact_ids = new_items.get('artifact', [])
                    list_api = "https://api.hakush.in/gi/data/artifact.json"
                elif game == Game.HSR: 
                    artifact_ids = new_items.get('relicset', [])
                    list_api = "https://api.hakush.in/hsr/data/relicset.json"
                elif game == Game.ZZZ: 
                    artifact_ids = new_items.get('equipment', [])
                    list_api = "https://api.hakush.in/zzz/data/equipment.json"
                
                if not artifact_ids:
                     await interaction.followup.send(f"❌ {game_name} 출시 예정 성유물/유물이 없어요.")
                     return

                # Fetch list API to get names
                async with session.get(list_api) as resp:
                    if resp.status != 200:
                        await interaction.followup.send("❌ 성유물 목록을 가져올 수 없어요.")
                        return
                    all_data = await resp.json()

                artifacts = []
                from types import SimpleNamespace
                
                for aid in artifact_ids[:6]:
                    art_data = all_data.get(str(aid))
                    if not art_data:
                        continue
                    
                    a = SimpleNamespace()
                    a.id = aid
                    
                    # Extract name based on game (same logic as _show_artifact_detail_by_id)
                    name = None
                    if game == Game.GI:
                        set_data = art_data.get('set', {})
                        if set_data:
                            first_set = next(iter(set_data.values()), {})
                            name = first_set.get('name', {}).get('KR') or first_set.get('name', {}).get('EN')
                    elif game == Game.HSR:
                        name = art_data.get('kr') or art_data.get('en')
                    elif game == Game.ZZZ:
                        ko_data = art_data.get('KO', {})
                        if isinstance(ko_data, dict):
                            name = ko_data.get('name')
                    
                    a.name = name or f"세트 #{aid}"
                    artifacts.append(a)
                
                if not artifacts:
                    await interaction.followup.send(f"❌ {game_name} 출시 예정 성유물 정보를 불러올 수 없어요.")
                    return

                color = GAME_COLORS.get(game, 0x9370DB)
                artifact_term = self._get_artifact_term(game)
                
                embed = discord.Embed(
                    title=f"🏺 {game_name} 출시 예정 {artifact_term} (v{new_items.get('version', '?')})",
                    description=f"총 {len(artifact_ids)}개 - 번호를 눌러 상세 정보 확인",
                    color=color
                )
                
                for i, art in enumerate(artifacts):
                    embed.add_field(name=f"{i+1}. {art.name}", value="세트 효과: 상세 보기", inline=False)
                
                embed.set_footer(text=f"데이터 출처: hakush.in | {game_name}")
                
                view = HoyoSelectView(self, artifacts, game, game_name, 'artifact')
                msg = await interaction.followup.send(embed=embed, view=view)
                view.message = msg
                
        except Exception as e:
            await interaction.followup.send(f"❌ 오류 발생: {e}")

    @app_commands.command(name="신성유물", description="출시 예정 성유물/유물/디스크를 확인해요")
    async def slash_new_artifact(self, interaction: discord.Interaction):
        embed = discord.Embed(title="🎮 게임 선택", description="관련 게임을 선택하세요:", color=0x5865F2)
        view = GameSelectView(self, "artifact")
        await interaction.response.send_message(embed=embed, view=view)
        view.message = await interaction.original_response()

    @commands.command(name="신성유물")
    async def new_artifact(self, ctx):
        embed = discord.Embed(title="🎮 게임 선택", description="관련 게임을 선택하세요:", color=0x5865F2)
        view = GameSelectView(self, "artifact")
        view.message = await ctx.send(embed=embed, view=view)

    @app_commands.command(name="성유물", description="성유물/유물/디스크 상세 정보를 확인해요")
    @app_commands.describe(name="이름 (예: 절연, 메신저, 펑크)")
    async def slash_artifact(self, interaction: discord.Interaction, name: str):
        await interaction.response.defer()
        results = await self._search_artifact_all_games(name)
        if not results:
            await interaction.followup.send(f"❌ **{name}** 성유물/유물을 찾을 수 없어요.")
            return
        
        if len(results) == 1:
            r = results[0]
            await self._show_artifact_detail_by_id(interaction, r["id"], r["game"], r["game_name"], r["name"])
        else:
            embed = discord.Embed(title=f"🎮 '{name}' - 게임 선택", description="여러 게임에서 항목을 찾았어요:", color=0x5865F2)
            for r in results: embed.add_field(name=r["game_name"], value=r["name"], inline=True)
            view = HoyoSelectView(self, results, results[0]["game"], results[0]["game_name"], 'artifact')
            msg = await interaction.followup.send(embed=embed, view=view)
            view.message = msg

    @commands.command(name="성유물", aliases=["유물", "장비", "디스크"])
    async def artifact(self, ctx, *, name: str = None):
        if not name:
            await ctx.send("❌ 이름을 입력해주세요.")
            return
        msg = await ctx.send(f"🔄 **{name}** 정보를 가져오는 중...")
        results = await self._search_artifact_all_games(name)
        if not results:
            await msg.edit(content=f"❌ **{name}** 성유물/유물을 찾을 수 없어요.")
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
            await self._show_artifact_detail_by_id(FakeInteraction(ctx.channel), r["id"], r["game"], r["game_name"], r["name"])
        else:
            view = HoyoSelectView(self, results, results[0]["game"], results[0]["game_name"], 'artifact')
            await msg.edit(content=None, view=view)
            view.message = msg

async def setup(bot):
    await bot.add_cog(HoyoArtifacts(bot))
