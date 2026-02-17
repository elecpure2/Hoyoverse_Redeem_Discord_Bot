"""
원신 캐릭터/무기/성유물 정보 조회 (Honey Hunter World)
hakushin 대체 모듈 - 버튼 UI 기반
"""
import discord
from discord.ext import commands
from discord import ui
import aiohttp
from utils.honeyhunter import (
    fetch_character_list, fetch_character_detail,
    fetch_weapon_list, fetch_weapon_detail,
    fetch_artifact_list, fetch_artifact_detail,
    fetch_new_content, fetch_skill_detail, fetch_constellation_details,
    search_items
)

# 원소별 색상
ELEMENT_COLORS = {
    'Pyro': 0xEF7A35, 'Hydro': 0x4CC2F1, 'Electro': 0xB08FC2,
    'Cryo': 0x9FD6E3, 'Anemo': 0x74C2A8, 'Geo': 0xF0B232,
    'Dendro': 0xA5C83B, 'None': 0x808080,
}


# ─── 버튼 View ────────────────────────────────────────

class CharacterView(ui.View):
    """캐릭터 상세 정보 버튼 UI"""
    def __init__(self, cog, detail, color):
        super().__init__(timeout=300)
        self.cog = cog
        self.detail = detail
        self.color = color

    @ui.button(label="⚔️ 전투 스킬", style=discord.ButtonStyle.primary)
    async def skills_btn(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.defer()
        session = await self.cog._get_session()
        d = self.detail
        embeds = []
        for sk in d['skills'][:3]:
            sd = await fetch_skill_detail(session, sk['path'])
            if not sd:
                continue
            e = discord.Embed(title=f"⚔️ {sk['name']}", color=self.color)
            if sd['description']:
                desc = sd['description']
                e.add_field(name="설명", value=desc[:1024], inline=False)
            if sd['stats_lv10']:
                stats = list(sd['stats_lv10'].items())[:8]
                text = "\n".join(f"• {k}: **{v}**" for k, v in stats)
                e.add_field(name="Lv.10 기준", value=text[:1024], inline=False)
            embeds.append(e)
        if embeds:
            await interaction.followup.send(embeds=embeds, ephemeral=True)
        else:
            await interaction.followup.send("❌ 스킬 정보를 불러올 수 없습니다.", ephemeral=True)

    @ui.button(label="📖 고유 특성", style=discord.ButtonStyle.primary)
    async def passives_btn(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.defer()
        session = await self.cog._get_session()
        d = self.detail
        e = discord.Embed(title=f"📖 {d['name']} — 고유 특성", color=self.color)
        for ps in d['passives'][:4]:
            sd = await fetch_skill_detail(session, ps['path'])
            if sd and sd['description']:
                desc = sd['description']
                e.add_field(name=ps['name'], value=desc[:500] + ("..." if len(desc) > 500 else ""), inline=False)
            else:
                e.add_field(name=ps['name'], value="(설명 없음)", inline=False)
        await interaction.followup.send(embed=e, ephemeral=True)

    @ui.button(label="🌟 운명의 자리", style=discord.ButtonStyle.primary)
    async def const_btn(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.defer()
        session = await self.cog._get_session()
        d = self.detail
        const_details = await fetch_constellation_details(session, d['constellations'])
        e = discord.Embed(title=f"🌟 {d['name']} — 운명의 자리", color=self.color)
        for i, c in enumerate(const_details[:6]):
            desc = c.get('description', '') or "(설명 없음)"
            if len(desc) > 300:
                desc = desc[:300] + "..."
            e.add_field(name=f"{i+1}. {c['name']}", value=desc, inline=False)
        await interaction.followup.send(embed=e, ephemeral=True)

    @ui.button(label="📦 육성재료", style=discord.ButtonStyle.secondary)
    async def mats_btn(self, interaction: discord.Interaction, button: ui.Button):
        d = self.detail
        e = discord.Embed(title=f"📦 {d['name']} — 육성재료", color=self.color)
        
        has_mats = False
        if d.get('ascension_mats'):
            label = "캐릭터 돌파" if d.get('talent_mats') else "총 육성 재료"
            text = "\n".join(f"• {name} **×{qty}**" if qty else f"• {name}" for name, qty in d['ascension_mats'])
            e.add_field(name=label, value=text[:1024], inline=False)
            has_mats = True
        if d.get('talent_mats'):
            text = "\n".join(f"• {name} **×{qty}**" if qty else f"• {name}" for name, qty in d['talent_mats'])
            e.add_field(name="특성(스킬) 돌파", value=text[:1024], inline=False)
            has_mats = True
        if not has_mats:
            e.description = "재료 정보가 없습니다."
        await interaction.response.send_message(embed=e, ephemeral=True)


# ─── 신캐 선택 View ──────────────────────────────────

class NewCharSelectView(ui.View):
    """신규 캐릭터 선택 UI"""
    def __init__(self, cog, characters, version):
        super().__init__(timeout=120)
        self.cog = cog
        self.version = version
        # 캐릭터별 버튼 동적 추가
        for i, char in enumerate(characters[:5]):
            btn = ui.Button(label=char['name'], style=discord.ButtonStyle.primary, custom_id=f"newchar_{i}")
            btn.callback = self._make_callback(char)
            self.add_item(btn)

    def _make_callback(self, char):
        async def callback(interaction: discord.Interaction):
            await interaction.response.defer()
            session = await self.cog._get_session()
            detail = await fetch_character_detail(session, char['slug'])
            if not detail:
                await interaction.followup.send("❌ 캐릭터 정보를 불러올 수 없습니다.")
                return
            embed, view = self.cog._build_character_response(detail)
            embed.title = f"🆕 {self.version} 신규 — {embed.title}"
            await interaction.followup.send(embed=embed, view=view)
        return callback


# ─── Cog ─────────────────────────────────────────────

class GenshinInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._char_cache = {}
        self._weapon_cache = {}
        self._artifact_cache = {}

    async def _get_session(self) -> aiohttp.ClientSession:
        if not hasattr(self.bot, '_hh_session') or self.bot._hh_session.closed:
            self.bot._hh_session = aiohttp.ClientSession()
        return self.bot._hh_session

    async def _ensure_char_cache(self):
        if not self._char_cache:
            session = await self._get_session()
            self._char_cache = await fetch_character_list(session)

    async def _ensure_weapon_cache(self):
        if not self._weapon_cache:
            session = await self._get_session()
            self._weapon_cache = await fetch_weapon_list(session)

    async def _ensure_artifact_cache(self):
        if not self._artifact_cache:
            session = await self._get_session()
            self._artifact_cache = await fetch_artifact_list(session)

    def cog_unload(self):
        if hasattr(self.bot, '_hh_session') and not self.bot._hh_session.closed:
            self.bot.loop.create_task(self.bot._hh_session.close())

    # ─── 공통: 캐릭터 embed + 버튼 View 생성 ──────────

    def _build_character_response(self, d):
        """캐릭터 기본 embed + 버튼 View를 반환. !캐릭터와 !신캐 모두 이걸 사용."""
        color = ELEMENT_COLORS.get(d['element'], 0x808080)

        title = f"{'★' * d['rarity']} {d['name']}"
        if d['title']:
            title += f" — {d['title']}"

        embed = discord.Embed(title=title, color=color, url=d['url'])
        embed.set_thumbnail(url=d['icon_url'])

        # 기본 정보
        info_lines = [
            f"⚔️ 무기: **{d['weapon_ko']}**",
            f"🔥 원소: **{d['element_ko']}**",
        ]
        if d.get('constellation'):
            info_lines.append(f"⭐ 별자리: {d['constellation']}")
        if d.get('association'):
            info_lines.append(f"📍 소속: {d['association']}")
        embed.add_field(name="기본 정보", value="\n".join(info_lines), inline=False)

        # 스킬 / 패시브 / 별자리 이름만 간단히

        # 전투 스킬
        if d['skills']:
            text = " · ".join(f"`{sk['name']}`" for sk in d['skills'][:4])
            embed.add_field(name="⚔️ 전투 스킬", value=text, inline=True)

        # 고유 특성
        if d['passives']:
            text = " · ".join(f"`{p['name']}`" for p in d['passives'][:4])
            embed.add_field(name="📖 고유 특성", value=text, inline=True)

        # 별자리
        if d['constellations']:
            text = "\n".join(f"{i+1}. {c['name']}" for i, c in enumerate(d['constellations'][:6]))
            embed.add_field(name="🌟 운명의 자리", value=text, inline=False)

        # 소개
        if d.get('description'):
            desc = d['description']
            embed.add_field(
                name="📝 소개",
                value=desc[:200] + ("..." if len(desc) > 200 else ""),
                inline=False
            )

        embed.set_image(url=d['splash_url'])
        embed.set_footer(text="데이터: Honey Hunter World · 버튼을 눌러 상세정보 확인")

        view = CharacterView(self, d, color)
        return embed, view

    # ─── 선택 유틸 ─────────────────────────────────────

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

    # 캐릭터/무기/성유물 명령어는 hoyo_info.py로 통합됨



    def _build_weapon_embed(self, d):
        rarity_colors = {5: 0xE8A63C, 4: 0xA66BBD, 3: 0x5C92C2, 2: 0x6AAA6A, 1: 0x808080}
        color = rarity_colors.get(d['rarity'], 0x808080)

        embed = discord.Embed(
            title=f"{'★' * d['rarity']} {d['name']}",
            color=color, url=d['url']
        )
        embed.set_thumbnail(url=d['icon_url'])

        info = f"⚔️ 타입: **{d['weapon_type_ko']}**\n"
        info += f"⚡ 기초 공격력: **{d['base_attack']}**\n"
        if d['substat_type']:
            info += f"📊 부옵션: {d['substat_type']} **{d['base_substat']}**"
        embed.add_field(name="기본 정보", value=info, inline=False)

        if d['affix_desc']:
            affix = f"**{d['affix_name']}**\n{d['affix_desc']}"
            embed.add_field(name="🔮 무기 효과 (1재련)", value=affix[:1024], inline=False)

        if d.get('description'):
            embed.add_field(name="📝 설명", value=d['description'][:500], inline=False)

        embed.set_footer(text="데이터: Honey Hunter World")
        return embed



    def _build_artifact_embed(self, d):
        embed = discord.Embed(
            title=f"{'★' * d['rarity']} {d['name']}",
            color=0xE8A63C, url=d['url']
        )
        embed.set_thumbnail(url=d['icon_url'])

        if d['two_piece']:
            embed.add_field(name="2세트 효과", value=d['two_piece'], inline=False)
        if d['four_piece']:
            embed.add_field(name="4세트 효과", value=d['four_piece'], inline=False)

        embed.set_footer(text="데이터: Honey Hunter World")
        return embed

    # 신캐/신무기/갱신 명령어는 hoyo_info.py로 통합됨


async def setup(bot):
    await bot.add_cog(GenshinInfo(bot))
