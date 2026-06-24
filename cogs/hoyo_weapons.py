import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import re
from cogs.hoyo_shared import Game, GAME_COLORS, GAME_URLS, clean_description, HoyoSelectView, GameSelectView
from utils import nanoka


class HoyoWeapons(commands.Cog):
    # 무기/광추 종류 한글화
    WEAPON_TYPE_KO = {
        'WEAPON_SWORD_ONE_HAND': '한손검', 'WEAPON_CLAYMORE': '양손검',
        'WEAPON_POLE': '장병기', 'WEAPON_BOW': '활', 'WEAPON_CATALYST': '법구',
        'Sword': '한손검', 'Claymore': '양손검', 'Polearm': '장병기',
        'Bow': '활', 'Catalyst': '법구',
    }
    # HSR 운명의 길 (광추 base_type 은 내부 영문명으로 옴)
    HSR_PATH_KO = {
        'Warrior': '파멸', 'Rogue': '수렵', 'Mage': '지식', 'Shaman': '조화',
        'Warlock': '공허', 'Knight': '보존', 'Priest': '풍요', 'Memory': '기억',
        # 영문 길 이름도 혹시 모르니 매핑
        'Destruction': '파멸', 'Hunt': '수렵', 'Erudition': '지식', 'Harmony': '조화',
        'Nihility': '공허', 'Preservation': '보존', 'Abundance': '풍요',
        'Remembrance': '기억', 'Elation': '환락', 'General': '일반',
    }

    def __init__(self, bot):
        self.bot = bot
        self._weapon_cache_gi = {}
        self._weapon_cache_hsr = {}
        self._weapon_cache_zzz = {}

    def _get_weapon_term(self, game: Game) -> str:
        if game == Game.HSR:
            return "광추"
        if game == Game.ZZZ:
            return "음동기"
        return "무기"

    @staticmethod
    def _parse_rarity(value) -> int:
        """rarity 값을 정수 별 개수로 변환. (GI/ZZZ: 정수, HSR: 'CombatPower...Rarity5' 같은 문자열)"""
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            m = re.search(r'\d+', value)
            if m:
                return int(m.group())
        return 4

    async def _load_all_weapon_caches(self):
        """게임별 무기/광추 이름→ID 캐시 로드 (nanoka 목록 JSON 기반)."""
        targets = [
            ("gi", self._weapon_cache_gi),
            ("hsr", self._weapon_cache_hsr),
            ("zzz", self._weapon_cache_zzz),
        ]
        async with aiohttp.ClientSession() as session:
            for game_key, cache in targets:
                if cache:
                    continue
                try:
                    version = await nanoka.get_version(session, game_key)
                    if not version:
                        continue
                    async with session.get(nanoka.weapon_list_url(game_key, version)) as resp:
                        if resp.status != 200:
                            continue
                        data = await resp.json()
                    if not isinstance(data, dict):
                        continue
                    for k, v in data.items():
                        name = v.get('ko') or v.get('en')
                        if not name:
                            continue
                        if game_key == "zzz":
                            name = name.replace("Item_Weapon_", "").replace("_Name", "").replace("_", " ")
                        cache[name.lower()] = str(k)
                except Exception as e:
                    print(f"[{game_key}] 무기 캐시 로드 실패: {e}")

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

    def _weapon_type_label(self, game: Game, data: dict) -> str | None:
        """상세 데이터에서 종류/운명의 길/특성 라벨(한글) 추출."""
        if game == Game.HSR:
            base_type = data.get('base_type')
            return self.HSR_PATH_KO.get(base_type, base_type)
        if game == Game.GI:
            wtype = data.get('weapon_type')
            return self.WEAPON_TYPE_KO.get(wtype, wtype)
        if game == Game.ZZZ:
            wtype = data.get('weapon_type')
            if isinstance(wtype, dict) and wtype:
                return list(wtype.values())[0]
            return self.WEAPON_TYPE_KO.get(wtype, wtype) if wtype else None
        return None

    def _refinement_field(self, game: Game, data: dict):
        """재련/스킬 (이름, 설명) 1단계 추출. 없으면 (None, None)."""
        if game == Game.GI:
            refs = data.get('refinement')
            if isinstance(refs, dict):
                ref1 = refs.get('1') or refs.get(1)
                if isinstance(ref1, dict):
                    name = ref1.get('name') or '무기 스킬'
                    desc = clean_description(ref1.get('desc', ''), ref1.get('param_list'))
                    return name, desc
        elif game == Game.HSR:
            refs = data.get('refinements')
            if isinstance(refs, dict):
                name = refs.get('name') or '광추 스킬'
                params = None
                level = refs.get('level')
                if isinstance(level, dict):
                    l1 = level.get('1') or level.get(1)
                    if isinstance(l1, dict):
                        params = l1.get('param_list')
                desc = clean_description(refs.get('desc', ''), params)
                return name, desc
        elif game == Game.ZZZ:
            talents = data.get('talents')
            if isinstance(talents, dict):
                t1 = talents.get('1') or talents.get(1)
                if isinstance(t1, dict):
                    name = t1.get('name') or '음동기 효과'
                    desc = clean_description(t1.get('desc', ''))
                    return name, desc
        return None, None

    async def _show_weapon_detail_by_id(self, interaction, weapon_id, game: Game, game_name: str):
        weapon_term = self._get_weapon_term(game)
        color = GAME_COLORS.get(game, 0xFFD700)
        game_key = GAME_URLS.get(game, "gi")

        async def send_msg(**kwargs):
            await interaction.followup.send(**kwargs)

        try:
            async with aiohttp.ClientSession() as session:
                version = await nanoka.get_version(session, game_key)
                if not version:
                    await send_msg(content=f"❌ {weapon_term} 정보를 가져올 수 없어요. (버전 조회 실패)")
                    return

                url = nanoka.weapon_detail_url(game_key, version, weapon_id)
                async with session.get(url) as resp:
                    if resp.status != 200:
                        await send_msg(content=f"❌ {weapon_term} 상세 정보를 가져올 수 없어요.")
                        return
                    data = await resp.json()

            name = data.get('name') or f"Unknown {weapon_id}"
            if game == Game.ZZZ and "Item_Weapon_" in name:
                name = name.replace("Item_Weapon_", "").replace("_Name", "").replace("_", " ")

            desc = clean_description(data.get('desc') or '') or "설명 없음"
            rarity = self._parse_rarity(data.get('rarity'))
            stars = '⭐' * rarity

            site = nanoka.site_url(game_key)
            detail_link = f"{site}{nanoka.WEAPON_ENDPOINT[game_key]}/{weapon_id}"

            icon_url = ""
            if game == Game.HSR:
                icon_url = nanoka.weapon_icon_url("hsr", weapon_id=weapon_id) or ""
            else:
                icon_url = nanoka.weapon_icon_url(game_key, icon=data.get('icon')) or ""

            embed = discord.Embed(
                title=f"{stars} {name}",
                description=f"{desc[:300]}\n\n[상세 정보 보기]({detail_link})",
                color=color,
            )
            if icon_url:
                embed.set_thumbnail(url=icon_url)

            # 종류 / 운명의 길 / 특성
            type_label = self._weapon_type_label(game, data)
            if type_label:
                field_name = "🛤️ 운명의 길" if game == Game.HSR else ("⚡ 특성" if game == Game.ZZZ else "⚔️ 종류")
                embed.add_field(name=field_name, value=type_label, inline=True)

            # 재련 / 스킬
            ref_name, ref_desc = self._refinement_field(game, data)
            if ref_desc:
                stack_label = "1중첩" if game == Game.HSR else ("1단계" if game == Game.ZZZ else "1재련")
                embed.add_field(name=f"🔮 {ref_name} ({stack_label})", value=ref_desc[:1024], inline=False)

            embed.set_footer(text=f"데이터 출처: nanoka.cc | {game_name}")
            await send_msg(embed=embed)

        except Exception as e:
            print(f"[무기상세] 오류: {e}")
            await send_msg(content=f"❌ 정보를 불러오는데 실패했어요: {e}")

    async def _show_new_weapons(self, interaction: discord.Interaction, game: Game, game_name: str):
        game_key = GAME_URLS.get(game, "gi")
        try:
            async with aiohttp.ClientSession() as session:
                manifest = await nanoka.fetch_manifest(session)
                if not manifest:
                    await interaction.followup.send("❌ 신규 데이터를 가져올 수 없어요.")
                    return

                game_block = manifest.get(game_key, {})
                version = game_block.get("latest")
                weapon_ids = game_block.get("new", {}).get(nanoka.WEAPON_ENDPOINT[game_key], [])

                if not weapon_ids:
                    await interaction.followup.send(f"❌ {game_name} 출시 예정 무기가 없어요.")
                    return

                weapons = []
                for wid in weapon_ids[:10]:
                    url = nanoka.weapon_detail_url(game_key, version, wid)
                    try:
                        async with session.get(url) as resp:
                            if resp.status != 200:
                                continue
                            d = await resp.json()
                        from types import SimpleNamespace
                        w = SimpleNamespace()
                        w.id = wid
                        w.name = d.get('name') or f"{wid}"
                        if game == Game.ZZZ:
                            w.name = w.name.replace("Item_Weapon_", "").replace("_Name", "").replace("_", " ")
                        w.rarity = self._parse_rarity(d.get('rarity'))
                        w._type_str = self._weapon_type_label(game, d) or "?"
                        weapons.append(w)
                    except Exception:
                        pass

                color = GAME_COLORS.get(game, 0x87CEEB)
                weapon_term = self._get_weapon_term(game)

                embed = discord.Embed(
                    title=f"⚔️ {game_name} · 출시 예정 {weapon_term}",
                    description=f"버전 {version or '?'} · 총 {len(weapon_ids)}개 · 아래 버튼으로 상세 정보를 확인하세요",
                    color=color,
                )

                for i, weapon in enumerate(weapons):
                    val = f"⭐ {getattr(weapon, 'rarity', 4)}성"
                    t = getattr(weapon, '_type_str', '')
                    if t and t != '?':
                        val += f"  ·  {t}"
                    embed.add_field(name=f"{i+1}.  {weapon.name}", value=val, inline=False)
                embed.set_footer(text="데이터 출처 · nanoka.cc")

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
            for r in results:
                embed.add_field(name=r["game_name"], value=r["name"], inline=True)
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
                    if 'embed' in kwargs:
                        await msg.edit(content=None, embed=kwargs['embed'])
                    elif 'content' in kwargs:
                        await msg.edit(content=kwargs['content'])

            await self._show_weapon_detail_by_id(FakeInteraction(ctx.channel), r["id"], r["game"], r["game_name"])
        else:
            view = HoyoSelectView(self, results, results[0]["game"], results[0]["game_name"], 'weapon')
            await msg.edit(content=None, view=view)
            view.message = msg


async def setup(bot):
    await bot.add_cog(HoyoWeapons(bot))
