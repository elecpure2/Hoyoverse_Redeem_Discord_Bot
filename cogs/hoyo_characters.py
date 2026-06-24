import discord
from discord.ext import commands
from discord import app_commands
import re
import aiohttp
from cogs.hoyo_shared import Game, GAME_COLORS, GAME_URLS, clean_description, HoyoSelectView, GameSelectView
from utils import nanoka

# 속성 한글화 (GI element / HSR damage_type 공용)
ELEMENT_KO = {
    'Anemo': '바람', 'Pyro': '불', 'Hydro': '물', 'Electro': '번개',
    'Cryo': '얼음', 'Geo': '바위', 'Dendro': '풀', 'None': '무',
    'Wind': '바람', 'Fire': '불', 'Water': '물', 'Thunder': '번개', 'Lightning': '번개',
    'Ice': '얼음', 'Rock': '바위', 'Grass': '풀',
    'Physical': '물리', 'Quantum': '양자', 'Imaginary': '허수',
    'Electric': '전기', 'Ether': '에테르',
}

# GI 무기 종류
GI_WEAPON_KO = {
    'WEAPON_SWORD_ONE_HAND': '한손검', 'WEAPON_CLAYMORE': '양손검',
    'WEAPON_POLE': '장병기', 'WEAPON_BOW': '활', 'WEAPON_CATALYST': '법구',
}

# HSR 운명의 길 (내부 영문명)
HSR_PATH_KO = {
    'Warrior': '파멸', 'Rogue': '수렵', 'Mage': '지식', 'Shaman': '조화',
    'Warlock': '공허', 'Knight': '보존', 'Priest': '풍요', 'Memory': '기억',
    'Destruction': '파멸', 'Hunt': '수렵', 'Erudition': '지식', 'Harmony': '조화',
    'Nihility': '공허', 'Preservation': '보존', 'Abundance': '풍요', 'Remembrance': '기억',
}

# 남은 파라미터 토큰(#1[i]% 등) 정리용
_LEFTOVER_PARAM = re.compile(r'#\d+\[[^\]]*\]%?')


def _clean_skill(desc: str, params=None) -> str:
    """스킬/돌파 설명 정리 (clean_description 래퍼)."""
    return clean_description(desc or '', params)


def _first_value(d):
    """{code: value} dict 의 첫 value 반환."""
    if isinstance(d, dict) and d:
        return next(iter(d.values()))
    return d


class HoyoCharacters(commands.Cog):
    # ZZZ rarity(int) -> 별 개수 (4=S급, 3=A급)
    ZZZ_RARITY_STARS = {4: 5, 3: 4, 2: 3}

    def __init__(self, bot):
        self.bot = bot
        self._char_cache_gi = {}
        self._char_cache_hsr = {}
        self._char_cache_zzz = {}

    # ─── 레어도 ─────────────────────────────────────────
    def _parse_rarity(self, game: Game, value) -> int:
        if game == Game.ZZZ:
            try:
                return self.ZZZ_RARITY_STARS.get(int(value), 5)
            except (TypeError, ValueError):
                return 5
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            if 'ORANGE' in value:
                return 5
            if 'PURPLE' in value:
                return 4
            m = re.search(r'\d+', value)
            if m:
                return int(m.group())
        return 5

    def _char_meta(self, game: Game, data: dict) -> str:
        """목록 카드용 짧은 메타 문자열 (예: '허수 · 수렵')."""
        if game == Game.GI:
            bits = [ELEMENT_KO.get(data.get('element'), data.get('element')),
                    GI_WEAPON_KO.get(data.get('weapon'), data.get('weapon'))]
        elif game == Game.HSR:
            bits = [ELEMENT_KO.get(data.get('damage_type'), data.get('damage_type')),
                    HSR_PATH_KO.get(data.get('base_type'), data.get('base_type'))]
        else:
            bits = [_first_value(data.get('element_type')), _first_value(data.get('weapon_type'))]
        return "  ·  ".join(str(b) for b in bits if b)

    # ─── 이름→ID 캐시 ───────────────────────────────────
    async def _load_all_char_caches(self):
        targets = [
            ("gi", self._char_cache_gi),
            ("hsr", self._char_cache_hsr),
            ("zzz", self._char_cache_zzz),
        ]
        async with aiohttp.ClientSession() as session:
            for game_key, cache in targets:
                if cache:
                    continue
                try:
                    version = await nanoka.get_version(session, game_key)
                    if not version:
                        continue
                    async with session.get(nanoka.char_list_url(game_key, version)) as resp:
                        if resp.status != 200:
                            continue
                        data = await resp.json()
                    if not isinstance(data, dict):
                        continue
                    for cid, cdata in data.items():
                        if not isinstance(cdata, dict):
                            continue
                        name = cdata.get('ko') or cdata.get('en')
                        if name:
                            cache[name.lower()] = str(cid)
                except Exception as e:
                    print(f"[{game_key}] 캐릭터 캐시 로드 실패: {e}")

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

    # ─── 상세 임베드 ─────────────────────────────────────
    def _build_embeds(self, game: Game, char_id, data: dict, game_name: str) -> list:
        game_key = GAME_URLS.get(game, "gi")
        color = GAME_COLORS.get(game, 0xFFD700)
        name = data.get('name') or f"캐릭터 {char_id}"
        stars = '⭐' * self._parse_rarity(game, data.get('rarity'))
        site = nanoka.site_url(game_key)
        char_path = "agent" if game == Game.ZZZ else "character"
        detail_link = f"{site}{char_path}/{char_id}"

        desc = clean_description(data.get('desc') or '')[:200]
        embed1 = discord.Embed(
            title=f"{stars} {name}",
            description=f"{desc}\n\n[상세 정보 보기]({detail_link})",
            color=color,
        )

        # 썸네일 + 기본 정보(속성/종류·길·특성)
        info_bits = []
        if game == Game.GI:
            icon = data.get('icon')
            thumb = nanoka.char_icon_url("gi", icon=icon)
            el = ELEMENT_KO.get(data.get('element'), data.get('element'))
            wp = GI_WEAPON_KO.get(data.get('weapon'), data.get('weapon'))
            if el:
                info_bits.append(f"**속성**: {el}")
            if wp:
                info_bits.append(f"**무기**: {wp}")
        elif game == Game.HSR:
            thumb = nanoka.char_icon_url("hsr", char_id=char_id)
            el = ELEMENT_KO.get(data.get('damage_type'), data.get('damage_type'))
            path = HSR_PATH_KO.get(data.get('base_type'), data.get('base_type'))
            if el:
                info_bits.append(f"**속성**: {el}")
            if path:
                info_bits.append(f"**운명의 길**: {path}")
        else:  # ZZZ
            icon = data.get('icon')
            thumb = nanoka.char_icon_url("zzz", icon=icon)
            el = _first_value(data.get('element_type'))
            sp = _first_value(data.get('weapon_type'))
            if el:
                info_bits.append(f"**속성**: {el}")
            if sp:
                info_bits.append(f"**특성**: {sp}")
        if thumb:
            embed1.set_thumbnail(url=thumb)
        if info_bits:
            embed1.add_field(name="기본 정보", value="\n".join(info_bits), inline=False)

        embeds = [embed1]

        # 스킬
        skill_fields = self._skill_fields(game, data)
        if skill_fields:
            es = discord.Embed(title=f"⚔️ {name} - 스킬", color=color)
            for sn, sd in skill_fields[:6]:
                es.add_field(name=f"🔹 {sn}", value=(sd or "설명 없음")[:1024], inline=False)
            embeds.append(es)

        # 돌파/성혼/시네마
        ascend_title, ascend_fields = self._ascension_fields(game, data, name)
        if ascend_fields:
            ea = discord.Embed(title=ascend_title, color=color)
            for an, ad in ascend_fields[:8]:
                ea.add_field(name=an, value=(ad or "설명 없음")[:1024], inline=False)
            embeds.append(ea)

        # 일러스트
        if game == Game.GI:
            illust = nanoka.char_illustration_url("gi", icon=data.get('icon'))
        elif game == Game.HSR:
            illust = nanoka.char_illustration_url("hsr", char_id=char_id)
        else:
            illust = nanoka.char_illustration_url("zzz", char_id=char_id)
        if illust:
            ei = discord.Embed(title=f"🎨 {name} 일러스트", color=color)
            ei.set_image(url=illust)
            ei.set_footer(text=f"데이터 출처: nanoka.cc | {game_name}")
            embeds.append(ei)
        else:
            embeds[-1].set_footer(text=f"데이터 출처: nanoka.cc | {game_name}")

        return embeds

    @staticmethod
    def _pick_by_level(level_dict, target):
        """{key:{'level':N,...}} 에서 level==target (없으면 target 이하 최대, 그것도 없으면 최소) 항목 반환."""
        if not isinstance(level_dict, dict) or not level_dict:
            return None
        entries = [v for v in level_dict.values() if isinstance(v, dict) and isinstance(v.get('level'), int)]
        if not entries:
            return None
        le = [v for v in entries if v['level'] <= target]
        return max(le, key=lambda v: v['level']) if le else min(entries, key=lambda v: v['level'])

    def _gi_skill_attrs(self, promote, target=10) -> list:
        """GI 스킬의 지정 레벨(기본 10) 데미지 배율(% 표기) 표를 추출."""
        entry = self._pick_by_level(promote, target)
        if not entry:
            return []
        param = entry.get('param', [])
        lines = []
        for item in entry.get('desc', []) or []:
            if not isinstance(item, str) or '|' not in item:
                continue
            label, tmpl = item.split('|', 1)
            val = clean_description(tmpl, param).strip()
            label = label.strip()
            if label and val and '%' in val:  # 데미지/배율(%) 위주
                lines.append(f"{label}: {val}")
        return lines[:10]

    def _skill_fields(self, game: Game, data: dict) -> list:
        out = []
        if game == Game.GI:
            for s in data.get('skills', []) or []:
                if isinstance(s, dict) and s.get('name'):
                    desc = _clean_skill(s.get('desc', ''))[:280]
                    attrs = self._gi_skill_attrs(s.get('promote'), 10)
                    val = desc
                    if attrs:
                        val = (desc + "\n\n**[Lv.10 데미지 배율]**\n" + "\n".join(attrs)).strip()
                    out.append((s['name'], val))
        elif game == Game.HSR:
            skills = data.get('skills', {})
            seen = set()
            for s in (skills.values() if isinstance(skills, dict) else []):
                if not isinstance(s, dict):
                    continue
                nm = s.get('name')
                if not nm or nm in seen:
                    continue
                seen.add(nm)
                params = None
                lv = self._pick_by_level(s.get('level'), 10)
                if isinstance(lv, dict):
                    params = lv.get('param_list')
                out.append((nm, _clean_skill(s.get('desc', ''), params)))
        else:  # ZZZ — skill dict(basic/dodge/special/chain/assist)의 실제 설명 사용
            skill = data.get('skill')
            if isinstance(skill, dict):
                for cat in ('basic', 'dodge', 'special', 'chain', 'assist'):
                    block = skill.get(cat)
                    descs = block.get('description', []) if isinstance(block, dict) else []
                    if not descs:
                        continue
                    # chain 은 궁극기 우선, 그 외엔 첫 항목
                    pick = next((x for x in descs if isinstance(x, dict) and '궁극기' in str(x.get('name', ''))), descs[0])
                    nm = pick.get('name')
                    dv = _clean_skill(pick.get('desc', ''))
                    if nm and dv:
                        out.append((nm, dv))
            # 코어 패시브
            passive = data.get('passive')
            if isinstance(passive, dict) and passive.get('name'):
                out.append((passive['name'], _clean_skill(passive.get('desc', ''))))
        return out

    def _ascension_fields(self, game: Game, data: dict, name: str):
        out = []
        if game == Game.GI:
            for i, c in enumerate(data.get('constellations', []) or []):
                if isinstance(c, dict) and c.get('name'):
                    out.append((f"{i+1}. {c['name']}", _clean_skill(c.get('desc', ''))))
            return f"✨ {name} - 운명의 자리", out
        if game == Game.HSR:
            ranks = data.get('ranks', {})
            if isinstance(ranks, dict):
                for k in sorted(ranks.keys(), key=lambda x: int(x) if str(x).isdigit() else 99):
                    r = ranks[k]
                    if isinstance(r, dict) and r.get('name'):
                        out.append((f"{k}. {r['name']}", _clean_skill(r.get('desc', ''), r.get('param_list'))))
            return f"✨ {name} - 성혼", out
        # ZZZ
        talent = data.get('talent', {})
        if isinstance(talent, dict):
            for k in sorted(talent.keys(), key=lambda x: int(x) if str(x).isdigit() else 99):
                t = talent[k]
                if isinstance(t, dict) and t.get('name'):
                    out.append((f"{k}. {t['name']}", _clean_skill(t.get('desc', ''), t.get('param') or t.get('params'))))
        return f"✨ {name} - 마인드스케이프 시네마", out

    async def _fetch_char_detail(self, game_key: str, char_id):
        async with aiohttp.ClientSession() as session:
            version = await nanoka.get_version(session, game_key)
            if not version:
                return None
            async with session.get(nanoka.char_detail_url(game_key, version, char_id)) as resp:
                if resp.status != 200:
                    return None
                return await resp.json()

    async def _show_character_detail_by_id(self, interaction, char_id, game: Game, game_name: str):
        async def send_func(content=None, embeds=None):
            if embeds:
                for i in range(0, len(embeds), 10):
                    await interaction.followup.send(embeds=embeds[i:i + 10])
            elif content:
                await interaction.followup.send(content=content)

        game_key = GAME_URLS.get(game, "gi")
        try:
            data = await self._fetch_char_detail(game_key, char_id)
            if not data:
                await send_func(content="❌ 상세 정보를 가져올 수 없어요.")
                return
            embeds = self._build_embeds(game, char_id, data, game_name)
            await send_func(embeds=embeds)
        except Exception as e:
            print(f"[캐릭터상세] 오류: {e}")
            await send_func(content=f"❌ 정보를 불러오는데 실패했어요: {e}")

    async def _show_new_characters(self, interaction: discord.Interaction, game: Game, game_name: str):
        game_key = GAME_URLS.get(game, "gi")
        try:
            async with aiohttp.ClientSession() as session:
                manifest = await nanoka.fetch_manifest(session)
                if not manifest:
                    await interaction.followup.send("❌ 신규 데이터를 가져올 수 없어요.")
                    return
                game_block = manifest.get(game_key, {})
                version = game_block.get("latest")
                char_ids = game_block.get("new", {}).get(nanoka.NEW_CHAR_KEY, [])
                if not char_ids:
                    await interaction.followup.send(f"❌ {game_name} 출시 예정 캐릭터가 없어요.")
                    return

                from types import SimpleNamespace
                chars = []
                for cid in char_ids[:10]:
                    url = nanoka.char_detail_url(game_key, version, cid)
                    try:
                        async with session.get(url) as resp:
                            if resp.status != 200:
                                continue
                            d = await resp.json()
                        c = SimpleNamespace()
                        c.id = cid
                        c.name = d.get('name') or f"{cid}"
                        c.rarity = self._parse_rarity(game, d.get('rarity'))
                        c.meta = self._char_meta(game, d)
                        chars.append(c)
                    except Exception:
                        pass

            color = GAME_COLORS.get(game, 0xFFD700)
            embed = discord.Embed(
                title=f"🌟 {game_name} · 출시 예정 캐릭터",
                description=f"버전 {version or '?'} · 총 {len(char_ids)}명 · 아래 버튼으로 상세 정보를 확인하세요",
                color=color,
            )
            for i, c in enumerate(chars):
                val = f"⭐ {getattr(c, 'rarity', 5)}성"
                meta = getattr(c, 'meta', '')
                if meta:
                    val += f"  ·  {meta}"
                embed.add_field(name=f"{i+1}.  {c.name}", value=val, inline=False)
            embed.set_footer(text="데이터 출처 · nanoka.cc")
            view = HoyoSelectView(self, chars, game, game_name, 'character')
            msg = await interaction.followup.send(embed=embed, view=view)
            view.message = msg
        except Exception as e:
            print(f"Error showing new chars: {e}")
            await interaction.followup.send(f"❌ 오류 발생: {e}")

    # ─── 명령어 ─────────────────────────────────────────
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
            r = results[0]
            await self._show_character_detail_by_id(interaction, r["id"], r["game"], r["game_name"])
        else:
            embed = discord.Embed(title=f"🎮 '{char_name}' - 게임 선택", description="여러 게임에서 캐릭터를 찾았어요:", color=0x5865F2)
            for r in results:
                embed.add_field(name=r["game_name"], value=r["name"], inline=True)
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
                        for e in kwargs['embeds'][1:]:
                            await ctx.send(embed=e)
                    elif 'embed' in kwargs:
                        await msg.edit(content=None, embed=kwargs['embed'])
                    elif 'content' in kwargs:
                        await msg.edit(content=kwargs['content'])

            await self._show_character_detail_by_id(FakeInteraction(ctx.channel), r["id"], r["game"], r["game_name"])
        else:
            view = HoyoSelectView(self, results, results[0]["game"], results[0]["game_name"], 'character')
            await msg.edit(content=None, view=view)
            view.message = msg


async def setup(bot):
    await bot.add_cog(HoyoCharacters(bot))
