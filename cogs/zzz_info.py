"""
젠레스 존 제로 에이전트/W-엔진/디스크 정보 조회 (Prydwen.gg)
버튼 UI 기반
"""
import discord
from discord.ext import commands
from discord import ui
import aiohttp
from utils.prydwen_zzz import (
    fetch_agent_list, fetch_agent_detail,
    fetch_wengine_list, fetch_disk_list,
    search_items, ELEMENT_KO, STYLE_KO,
)

# 속성별 색상
ELEMENT_COLORS = {
    'Physical': 0xE8A63C, 'Fire': 0xE8583B, 'Ice': 0x47C7FD,
    'Electric': 0xC86EDF, 'Ether': 0xFFA500,
}

RARITY_COLORS = {'S': 0xE8A63C, 'A': 0xA66BBD, 'B': 0x5C92C2}


# ─── 버튼 View ────────────────────────────────────────

class ZZZAgentView(ui.View):
    """젠존제 에이전트 상세 버튼 UI"""
    def __init__(self, detail, color):
        super().__init__(timeout=300)
        self.detail = detail
        self.color = color

    @ui.button(label="🎬 마인드스케이프 시네마", style=discord.ButtonStyle.primary)
    async def talents_btn(self, interaction: discord.Interaction, button: ui.Button):
        d = self.detail
        e = discord.Embed(title=f"🎬 {d['name']} — 마인드스케이프 시네마", color=self.color)
        for i, t in enumerate(d['talents'][:6]):
            desc = t['description'] or "(설명 없음)"
            if len(desc) > 300:
                desc = desc[:300] + "..."
            e.add_field(name=f"M{i+1}. {t['name']}", value=desc, inline=False)
        if not d['talents']:
            e.description = "마인드스케이프 시네마 정보가 없습니다."
        await interaction.response.send_message(embed=e, ephemeral=True)


# ─── Cog ─────────────────────────────────────────────

class ZZZInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._agent_cache = {}
        self._wengine_cache = {}
        self._disk_cache = {}

    async def _get_session(self) -> aiohttp.ClientSession:
        if not hasattr(self.bot, '_prydwen_zzz_session') or self.bot._prydwen_zzz_session.closed:
            self.bot._prydwen_zzz_session = aiohttp.ClientSession()
        return self.bot._prydwen_zzz_session

    async def _ensure_agent_cache(self):
        if not self._agent_cache:
            session = await self._get_session()
            self._agent_cache = await fetch_agent_list(session)

    async def _ensure_wengine_cache(self):
        if not self._wengine_cache:
            session = await self._get_session()
            self._wengine_cache = await fetch_wengine_list(session)

    async def _ensure_disk_cache(self):
        if not self._disk_cache:
            session = await self._get_session()
            self._disk_cache = await fetch_disk_list(session)

    def cog_unload(self):
        if hasattr(self.bot, '_prydwen_zzz_session') and not self.bot._prydwen_zzz_session.closed:
            self.bot.loop.create_task(self.bot._prydwen_zzz_session.close())

    # ─── 선택 유틸 ─────────────────────────────

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

    # ─── 에이전트 embed + View ──────────────────────────

    def _build_agent_response(self, d):
        color = ELEMENT_COLORS.get(d['element'], 0x808080)
        rarity_star = "S" if d['rarity'] == 'S' else "A"
        title = f"【{rarity_star}】 {d['name']}"
        if d['name'] != d['name_en']:
            title += f" ({d['name_en']})"

        embed = discord.Embed(title=title, color=color, url=d['url'])

        info_lines = [
            f"⚡ 속성: **{d['element_ko']}**",
            f"🎯 전투 스타일: **{d['style_ko']}** ({d['style']})",
        ]
        if d.get('faction'):
            info_lines.append(f"📍 소속: {d['faction']}")
        if d.get('full_name') and d['full_name'] != d['name_en']:
            info_lines.append(f"👤 풀네임: {d['full_name']}")
        if d.get('voice_kr'):
            info_lines.append(f"🎤 한국어 CV: {d['voice_kr']}")
        embed.add_field(name="기본 정보", value="\n".join(info_lines), inline=False)

        # 마인드스케이프 이름
        if d['talents']:
            text = "\n".join(f"M{i+1}. {t['name']}" for i, t in enumerate(d['talents'][:6]))
            embed.add_field(name="🎬 마인드스케이프 시네마", value=text, inline=False)

        if d.get('introduction'):
            intro = d['introduction']
            embed.add_field(
                name="📝 소개",
                value=intro[:200] + ("..." if len(intro) > 200 else ""),
                inline=False
            )

        embed.set_footer(text="데이터: Prydwen.gg · 버튼을 눌러 상세정보 확인")
        view = ZZZAgentView(d, color)
        return embed, view

    # 에이전트/W-엔진/디스크 명령어는 hoyo_info.py로 통합됨

    # ─── 캐시 초기화 ─────────────────────────────────────

    @commands.command(name="젠갱신")
    @commands.has_permissions(administrator=True)
    async def refresh_zzz_cache(self, ctx):
        """젠존제 캐시 초기화 (관리자 전용)"""
        self._agent_cache = {}
        self._wengine_cache = {}
        self._disk_cache = {}
        await ctx.send("✅ 젠존제 캐시가 초기화되었습니다.")


async def setup(bot):
    await bot.add_cog(ZZZInfo(bot))
