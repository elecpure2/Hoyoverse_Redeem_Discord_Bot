"""
붕괴: 스타레일 캐릭터/광추/유물 정보 조회 (Prydwen.gg)
버튼 UI 기반
"""
import discord
from discord.ext import commands
from discord import ui
import aiohttp
from utils.prydwen_hsr import (
    fetch_character_list, fetch_character_detail,
    fetch_lightcone_list, fetch_lightcone_detail,
    fetch_relic_list, load_kr_names,
    search_items, ELEMENT_KO, PATH_KO,
)

# 원소별 색상
ELEMENT_COLORS = {
    'Physical': 0xC0C0C0, 'Fire': 0xE8583B, 'Ice': 0x47C7FD,
    'Lightning': 0xC86EDF, 'Wind': 0x55D884, 'Quantum': 0x7B68EE,
    'Imaginary': 0xF5D442,
}

RARITY_COLORS = {5: 0xE8A63C, 4: 0xA66BBD, 3: 0x5C92C2}


# ─── 버튼 View ────────────────────────────────────────

class HSRCharacterView(ui.View):
    """스타레일 캐릭터 상세 정보 버튼 UI"""
    def __init__(self, detail, color):
        super().__init__(timeout=300)
        self.detail = detail
        self.color = color

    @ui.button(label="⚔️ 전투 스킬", style=discord.ButtonStyle.primary)
    async def skills_btn(self, interaction: discord.Interaction, button: ui.Button):
        d = self.detail
        e = discord.Embed(title=f"⚔️ {d['name']} — 전투 스킬", color=self.color)
        for sk in d['skills']:
            energy = f" (에너지: {sk['energy']})" if sk.get('energy') else ""
            name_part = sk.get('name', '')
            field_name = f"{sk['type_ko']}: {name_part}{energy}" if name_part else f"{sk['type_ko']}{energy}"
            desc = sk.get('desc', '') or f"타입: `{sk['type']}`"
            if len(desc) > 1024:
                desc = desc[:1021] + "..."
            e.add_field(
                name=field_name,
                value=desc,
                inline=False,
            )
        if not d['skills']:
            e.description = "스킬 정보가 없습니다."
        await interaction.response.send_message(embed=e, ephemeral=True)

    @ui.button(label="🌟 에이도론", style=discord.ButtonStyle.primary)
    async def eidolons_btn(self, interaction: discord.Interaction, button: ui.Button):
        d = self.detail
        e = discord.Embed(title=f"🌟 {d['name']} — 에이도론", color=self.color)
        for i, eid in enumerate(d['eidolons'][:6]):
            desc = eid['description'] or "(설명 없음)"
            if len(desc) > 300:
                desc = desc[:300] + "..."
            e.add_field(name=f"E{i+1}. {eid['name']}", value=desc, inline=False)
        if not d['eidolons']:
            e.description = "에이도론 정보가 없습니다."
        await interaction.response.send_message(embed=e, ephemeral=True)

    @ui.button(label="📖 트레이스", style=discord.ButtonStyle.primary)
    async def traces_btn(self, interaction: discord.Interaction, button: ui.Button):
        d = self.detail
        e = discord.Embed(title=f"📖 {d['name']} — 트레이스 (패시브)", color=self.color)
        for t in d['traces'][:4]:
            desc = t['desc'] or "(설명 없음)"
            if len(desc) > 400:
                desc = desc[:400] + "..."
            e.add_field(name=f"🔓 {t['req']}", value=desc, inline=False)
        if not d['traces']:
            e.description = "트레이스 정보가 없습니다."
        await interaction.response.send_message(embed=e, ephemeral=True)

    @ui.button(label="📦 육성재료", style=discord.ButtonStyle.secondary)
    async def mats_btn(self, interaction: discord.Interaction, button: ui.Button):
        d = self.detail
        e = discord.Embed(title=f"📦 {d['name']} — 육성재료", color=self.color)
        if d.get('ascension_mats'):
            text = "\n".join(f"• {m.replace('-', ' ').title()}" for m in d['ascension_mats'])
            e.add_field(name="돌파 재료", value=text[:1024], inline=False)
        else:
            e.description = "재료 정보가 없습니다."
        await interaction.response.send_message(embed=e, ephemeral=True)


# ─── Cog ─────────────────────────────────────────────

class HSRInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._char_cache = {}
        self._lc_cache = {}
        self._relic_cache = {}

    async def _get_session(self) -> aiohttp.ClientSession:
        if not hasattr(self.bot, '_prydwen_session') or self.bot._prydwen_session.closed:
            self.bot._prydwen_session = aiohttp.ClientSession()
        return self.bot._prydwen_session

    async def _ensure_char_cache(self):
        if not self._char_cache:
            session = await self._get_session()
            await load_kr_names(session)  # StarRailRes에서 공식 한글 이름 로드
            self._char_cache = await fetch_character_list(session)

    async def _ensure_lc_cache(self):
        if not self._lc_cache:
            session = await self._get_session()
            self._lc_cache = await fetch_lightcone_list(session)

    async def _ensure_relic_cache(self):
        if not self._relic_cache:
            session = await self._get_session()
            self._relic_cache = await fetch_relic_list(session)

    def cog_unload(self):
        if hasattr(self.bot, '_prydwen_session') and not self.bot._prydwen_session.closed:
            self.bot.loop.create_task(self.bot._prydwen_session.close())

    # ─── 공통: 선택 유틸 ─────────────────────────────

    async def _select_from_results(self, ctx, results, query):
        if len(results) == 1:
            return results[0]

        desc = "\n".join(f"**{i+1}.** {n}" for i, (n, _) in enumerate(results[:10]))
        embed = discord.Embed(
            title=f"🔍 '{query}' 검색 결과",
            description=desc + "\n\n번호를 입력하세요 (15초)",
            color=0x5865F2
        )
        await ctx.send(embed=embed)

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content.isdigit()

        try:
            reply = await self.bot.wait_for("message", check=check, timeout=15)
            idx = int(reply.content) - 1
            if 0 <= idx < len(results):
                return results[idx]
            await ctx.send("❌ 잘못된 번호입니다.")
        except Exception:
            await ctx.send("⏰ 시간 초과")
        return None

    # ─── 캐릭터 embed + View ──────────────────────────

    def _build_character_response(self, d):
        color = ELEMENT_COLORS.get(d['element'], 0x808080)
        title = f"{'★' * d['rarity']} {d['name']}"
        if d['name'] != d['name_en']:
            title += f" ({d['name_en']})"

        embed = discord.Embed(title=title, color=color, url=d['url'])

        info_lines = [
            f"⚔️ 운명: **{d['path_ko']}** ({d['path']})",
            f"🔥 속성: **{d['element_ko']}**",
        ]
        if d.get('affiliation'):
            info_lines.append(f"📍 소속: {d['affiliation']}")
        if d.get('energy_ult'):
            info_lines.append(f"⚡ 필살기 에너지: {d['energy_ult']}")
        embed.add_field(name="기본 정보", value="\n".join(info_lines), inline=False)

        # 스탯
        stats = d.get('stats', {})
        if stats:
            stat_text = " · ".join([
                f"HP `{stats.get('hp_base', '?')}`",
                f"ATK `{stats.get('atk_base', '?')}`",
                f"DEF `{stats.get('def_base', '?')}`",
                f"SPD `{stats.get('speed_base', '?')}`",
            ])
            embed.add_field(name="📊 기본 스탯 (Lv.80)", value=stat_text, inline=False)

        # 스킬 이름
        if d['skills']:
            lines = []
            for sk in d['skills']:
                name_part = sk.get('name', '')
                if name_part:
                    lines.append(f"`{sk['type_ko']}` {name_part}")
                else:
                    lines.append(f"`{sk['type_ko']}`")
            embed.add_field(name="⚔️ 전투 스킬", value="\n".join(lines), inline=False)

        # 에이도론 이름
        if d['eidolons']:
            text = "\n".join(f"E{i+1}. {e['name']}" for i, e in enumerate(d['eidolons'][:6]))
            embed.add_field(name="🌟 에이도론", value=text, inline=False)

        if d.get('description'):
            desc = d['description']
            embed.add_field(
                name="📝 소개",
                value=desc[:200] + ("..." if len(desc) > 200 else ""),
                inline=False
            )

        embed.set_footer(text="데이터: Prydwen.gg + StarRailRes · 버튼을 눌러 상세정보 확인")
        view = HSRCharacterView(d, color)
        return embed, view

    # 캐릭터/광추/유물 명령어는 hoyo_info.py로 통합됨

    def _build_lightcone_embed(self, lc_name, lc_info):
        """광추 embed 빌드 (통합 cog에서 호출)"""
        rarity = lc_info.get('rarity', 4)
        color = RARITY_COLORS.get(rarity, 0x808080)
        stars = '★' * rarity
        title = f"{stars} {lc_name}"
        if lc_info.get('name_en') and lc_info['name_en'] != lc_name:
            title += f" ({lc_info['name_en']})"
        embed = discord.Embed(title=title, color=color)
        path = lc_info.get('path', '')
        path_ko = PATH_KO.get(path, path)
        info = f"🛤️ 운명: **{path_ko}** ({path})"
        embed.add_field(name="기본 정보", value=info, inline=False)
        if lc_info.get('description'):
            desc = lc_info['description']
            embed.add_field(name="📖 설명", value=desc[:1024], inline=False)
        if lc_info.get('superimpose'):
            embed.add_field(name="🔮 광추 효과", value=lc_info['superimpose'][:1024], inline=False)
        embed.set_footer(text="데이터: Prydwen.gg + StarRailRes")
        return embed

    # ─── 유물 세트 ──────────────────────────────────────

    def _build_relic_embed(self, relic_name, relic_info):
        """유물 세트 embed 빌드 (통합 cog에서 호출)"""
        embed = discord.Embed(title=f"🏺 {relic_name}", color=0xE8A63C)
        embed.add_field(name="타입", value=relic_info.get('type', '?'), inline=False)
        if relic_info.get('bonus2'):
            embed.add_field(name="2세트 효과", value=relic_info['bonus2'][:1024], inline=False)
        if relic_info.get('bonus4'):
            embed.add_field(name="4세트 효과", value=relic_info['bonus4'][:1024], inline=False)
        embed.set_footer(text="데이터: Prydwen.gg")
        return embed

    # ─── 캐시 초기화 ─────────────────────────────────────

    @commands.command(name="스타갱신")
    @commands.has_permissions(administrator=True)
    async def refresh_hsr_cache(self, ctx):
        """스타레일 캐시 초기화 (관리자 전용)"""
        self._char_cache = {}
        self._lc_cache = {}
        self._relic_cache = {}
        await ctx.send("✅ 스타레일 캐시가 초기화되었습니다.")


async def setup(bot):
    await bot.add_cog(HSRInfo(bot))
