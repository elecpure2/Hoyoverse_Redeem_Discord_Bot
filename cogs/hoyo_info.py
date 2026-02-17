"""
호요버스 통합 정보 조회 Cog
!캐릭터, !무기, !성유물 명령어로 원신/스타레일/젠존제 3게임 통합 검색
이름이 겹치면 게임 선택 드롭다운 표시
"""
import discord
from discord.ext import commands
from discord import ui
import aiohttp


# 게임별 이모지/색상
GAME_INFO = {
    'gi':  {'name': '원신', 'emoji': '🌀', 'color': 0x00BFFF},
    'hsr': {'name': '스타레일', 'emoji': '🚂', 'color': 0xCDA0E0},
    'zzz': {'name': '젠존제', 'emoji': '📺', 'color': 0xE8A63C},
}


# ─── 게임 선택 드롭다운 ────────────────────────────────────

class GameSelectView(ui.View):
    """여러 게임에서 결과가 나왔을 때 게임 선택 드롭다운"""
    def __init__(self, cog, ctx, matches, category):
        super().__init__(timeout=30)
        self.cog = cog
        self.ctx = ctx
        self.matches = matches  # [(game_key, name, data), ...]
        self.category = category

        options = []
        for game_key, name, _ in matches:
            gi = GAME_INFO[game_key]
            options.append(discord.SelectOption(
                label=f"{gi['name']} — {name}",
                value=game_key,
                emoji=gi['emoji']
            ))
        select = ui.Select(placeholder="게임을 선택하세요", options=options)
        select.callback = self._select_callback
        self.add_item(select)

    async def _select_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        game_key = interaction.data['values'][0]
        for gk, name, data in self.matches:
            if gk == game_key:
                await self.cog._show_result(interaction, gk, name, data, self.category)
                return

    async def interaction_check(self, interaction):
        return interaction.user == self.ctx.author


# ─── 통합 Cog ─────────────────────────────────────────

class HoyoInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def _get_gi_cog(self):
        return self.bot.get_cog('GenshinInfo')

    def _get_hsr_cog(self):
        return self.bot.get_cog('HSRInfo')

    def _get_zzz_cog(self):
        return self.bot.get_cog('ZZZInfo')

    # ─── 통합 검색 ──────────────────────────────────────

    async def _search_all_games(self, name, category):
        """3게임에서 이름 검색. category: 'character', 'weapon', 'artifact'"""
        matches = []  # [(game_key, display_name, data)]

        # ── 원신 ──
        gi = self._get_gi_cog()
        if gi:
            if category == 'character':
                await gi._ensure_char_cache()
                from utils.honeyhunter import search_items as gi_search
                results = gi_search(name, gi._char_cache)
                for n, d in results[:3]:
                    matches.append(('gi', n, d))
            elif category == 'weapon':
                await gi._ensure_weapon_cache()
                from utils.honeyhunter import search_items as gi_search
                results = gi_search(name, gi._weapon_cache)
                for n, d in results[:3]:
                    matches.append(('gi', n, d))
            elif category == 'artifact':
                await gi._ensure_artifact_cache()
                from utils.honeyhunter import search_items as gi_search
                results = gi_search(name, gi._artifact_cache)
                for n, d in results[:3]:
                    matches.append(('gi', n, d))

        # ── HSR ──
        hsr = self._get_hsr_cog()
        if hsr:
            if category == 'character':
                await hsr._ensure_char_cache()
                from utils.prydwen_hsr import search_items as hsr_search
                results = hsr_search(name, hsr._char_cache)
                for n, d in results[:3]:
                    matches.append(('hsr', n, d))
            elif category == 'weapon':
                await hsr._ensure_lc_cache()
                from utils.prydwen_hsr import search_items as hsr_search
                results = hsr_search(name, hsr._lc_cache)
                for n, d in results[:3]:
                    matches.append(('hsr', n, d))
            elif category == 'artifact':
                await hsr._ensure_relic_cache()
                from utils.prydwen_hsr import search_items as hsr_search
                results = hsr_search(name, hsr._relic_cache)
                for n, d in results[:3]:
                    matches.append(('hsr', n, d))

        # ── ZZZ ──
        zzz = self._get_zzz_cog()
        if zzz:
            if category == 'character':
                await zzz._ensure_agent_cache()
                from utils.prydwen_zzz import search_items as zzz_search
                results = zzz_search(name, zzz._agent_cache)
                for n, d in results[:3]:
                    matches.append(('zzz', n, d))
            elif category == 'weapon':
                await zzz._ensure_wengine_cache()
                from utils.prydwen_zzz import search_items as zzz_search
                results = zzz_search(name, zzz._wengine_cache)
                for n, d in results[:3]:
                    matches.append(('zzz', n, d))
            elif category == 'artifact':
                await zzz._ensure_disk_cache()
                from utils.prydwen_zzz import search_items as zzz_search
                results = zzz_search(name, zzz._disk_cache)
                for n, d in results[:3]:
                    matches.append(('zzz', n, d))

        return matches

    async def _show_result(self, ctx_or_interaction, game_key, name, data, category):
        """게임별 결과 표시 — 각 게임 Cog의 기존 로직 재사용"""
        is_interaction = isinstance(ctx_or_interaction, discord.Interaction)

        # 헬퍼: interaction은 followup (이미 defer 완료), ctx는 send
        async def _send(embed, view=None):
            if is_interaction:
                if view:
                    await ctx_or_interaction.followup.send(embed=embed, view=view)
                else:
                    await ctx_or_interaction.followup.send(embed=embed)
            else:
                if view:
                    await ctx_or_interaction.send(embed=embed, view=view)
                else:
                    await ctx_or_interaction.send(embed=embed)

        async def _send_error(msg):
            if is_interaction:
                await ctx_or_interaction.followup.send(msg, ephemeral=True)
            else:
                await ctx_or_interaction.send(msg)

        if game_key == 'gi':
            gi = self._get_gi_cog()
            if not gi:
                return
            session = await gi._get_session()

            if category == 'character':
                from utils.honeyhunter import fetch_character_detail
                detail = await fetch_character_detail(session, data)
                if not detail:
                    await _send_error("❌ 캐릭터 정보를 불러올 수 없습니다.")
                    return
                embed, view = gi._build_character_response(detail)
            elif category == 'weapon':
                from utils.honeyhunter import fetch_weapon_detail
                slug, _ = data
                detail = await fetch_weapon_detail(session, slug)
                if not detail:
                    await _send_error("❌ 무기 정보를 불러올 수 없습니다.")
                    return
                embed = gi._build_weapon_embed(detail)
                view = None
            elif category == 'artifact':
                from utils.honeyhunter import fetch_artifact_detail
                detail = await fetch_artifact_detail(session, data)
                if not detail:
                    await _send_error("❌ 성유물 정보를 불러올 수 없습니다.")
                    return
                embed = gi._build_artifact_embed(detail)
                view = None

        elif game_key == 'hsr':
            hsr = self._get_hsr_cog()
            if not hsr:
                return
            session = await hsr._get_session()

            if category == 'character':
                from utils.prydwen_hsr import fetch_character_detail
                detail = await fetch_character_detail(session, data['slug'])
                if not detail:
                    await _send_error("❌ 캐릭터 정보를 불러올 수 없습니다.")
                    return
                embed, view = hsr._build_character_response(detail)
            elif category == 'weapon':
                embed = hsr._build_lightcone_embed(name, data)
                view = None
            elif category == 'artifact':
                embed = hsr._build_relic_embed(name, data)
                view = None

        elif game_key == 'zzz':
            zzz = self._get_zzz_cog()
            if not zzz:
                return
            session = await zzz._get_session()

            if category == 'character':
                from utils.prydwen_zzz import fetch_agent_detail, ELEMENT_KO, STYLE_KO
                detail = await fetch_agent_detail(session, data['slug'])
                if not detail:
                    await _send_error("❌ 에이전트 정보를 불러올 수 없습니다.")
                    return
                embed, view = zzz._build_agent_response(detail)
            elif category == 'weapon':
                from utils.prydwen_zzz import ELEMENT_KO, STYLE_KO
                color_map = {'S': 0xE8A63C, 'A': 0xA66BBD, 'B': 0x5C92C2}
                color = color_map.get(data.get('rarity', 'A'), 0x808080)
                embed = discord.Embed(title=f"【{data.get('rarity','A')}】 {name}", color=color)
                info = f"⚡ 속성: **{ELEMENT_KO.get(data.get('element',''), data.get('element',''))}**\n"
                info += f"🎯 타입: **{data.get('type_ko', data.get('type', ''))}**"
                embed.add_field(name="기본 정보", value=info, inline=False)
                stats = data.get('stats', {})
                if stats:
                    stat_text = f"ATK: {stats.get('base_atk','?')} ~ {stats.get('max_atk','?')}"
                    if stats.get('stat'):
                        stat_text += f"\n{stats['stat']}: {stats.get('base_special','?')} ~ {stats.get('max_special','?')}"
                    embed.add_field(name="📊 스탯", value=stat_text, inline=False)
                if data.get('talent_name'):
                    txt = f"**{data['talent_name']}**"
                    if data.get('description'):
                        txt += f"\n{data['description'][:500]}"
                    embed.add_field(name="🔮 W-엔진 효과", value=txt[:1024], inline=False)
                embed.set_footer(text="데이터: Prydwen.gg")
                view = None
            elif category == 'artifact':
                embed = discord.Embed(title=f"💿 {name}", color=0xE8A63C)
                if data.get('bonus2'):
                    embed.add_field(name="2세트 효과", value=data['bonus2'][:1024], inline=False)
                if data.get('bonus4'):
                    embed.add_field(name="4세트 효과", value=data['bonus4'][:1024], inline=False)
                embed.set_footer(text="데이터: Prydwen.gg")
                view = None

        await _send(embed, view)

    async def _handle_search(self, ctx, name, category, category_ko):
        """통합 검색 + 결과 처리"""
        async with ctx.typing():
            matches = await self._search_all_games(name, category)

            if not matches:
                await ctx.send(f"❌ '{name}'에 해당하는 {category_ko}를 찾을 수 없습니다.")
                return

            # 어떤 게임에서 나왔는지 확인
            game_keys = set(gk for gk, _, _ in matches)

            if len(game_keys) == 1:
                # 한 게임에서만 나옴 → 바로 표시
                if len(matches) == 1:
                    gk, n, d = matches[0]
                    await self._show_result(ctx, gk, n, d, category)
                else:
                    # 같은 게임에서 여러 결과
                    gk = matches[0][0]
                    gi = GAME_INFO[gk]
                    desc = "\n".join(f"**{i+1}.** {gi['emoji']} {n}" for i, (_, n, _) in enumerate(matches[:10]))
                    embed = discord.Embed(
                        title=f"🔍 '{name}' 검색 결과 ({gi['name']})",
                        description=desc + "\n\n번호를 입력하세요 (15초)",
                        color=gi['color']
                    )
                    await ctx.send(embed=embed)

                    def check(m):
                        return m.author == ctx.author and m.channel == ctx.channel and m.content.isdigit()
                    try:
                        reply = await self.bot.wait_for("message", check=check, timeout=15)
                        idx = int(reply.content) - 1
                        if 0 <= idx < len(matches):
                            _, n, d = matches[idx]
                            await self._show_result(ctx, gk, n, d, category)
                        else:
                            await ctx.send("❌ 잘못된 번호입니다.")
                    except Exception:
                        await ctx.send("⏰ 시간 초과")

            else:
                # 여러 게임에서 나옴 → 게임 선택 드롭다운
                # 각 게임에서 가장 좋은 결과 1개씩만
                best_per_game = {}
                for gk, n, d in matches:
                    if gk not in best_per_game:
                        best_per_game[gk] = (gk, n, d)
                best_matches = list(best_per_game.values())

                desc = "\n".join(
                    f"{GAME_INFO[gk]['emoji']} **{GAME_INFO[gk]['name']}** — {n}"
                    for gk, n, _ in best_matches
                )
                embed = discord.Embed(
                    title=f"🔍 '{name}' — 여러 게임에서 발견",
                    description=desc + "\n\n아래 드롭다운에서 게임을 선택하세요",
                    color=0x5865F2
                )
                view = GameSelectView(self, ctx, best_matches, category)
                await ctx.send(embed=embed, view=view)

    @commands.command(name="캐릭터")
    async def character(self, ctx, *, name: str):
        """캐릭터 검색 — 원신/스타레일/젠존제 통합 (예: !캐릭터 카프카)"""
        await self._handle_search(ctx, name, 'character', '캐릭터')

    @commands.command(name="무기")
    async def weapon(self, ctx, *, name: str):
        """무기 검색 — 원신 무기/스타레일 광추/젠존제 W-엔진 통합 (예: !무기 천공의 검)"""
        await self._handle_search(ctx, name, 'weapon', '무기')

    @commands.command(name="성유물", aliases=["유물"])
    async def artifact(self, ctx, *, name: str):
        """유물 검색 — 원신 성유물/스타레일 유물/젠존제 디스크 통합 (예: !성유물 절연)"""
        await self._handle_search(ctx, name, 'artifact', '유물')

    # ─── 신규 콘텐츠 (게임 선택 드롭다운) ──────────────────

    @commands.command(name="신캐", aliases=["신캐릭터"])
    async def new_characters(self, ctx):
        """신규 캐릭터 — 게임 선택 후 확인"""
        embed = discord.Embed(
            title="🆕 신규 캐릭터 조회",
            description="어떤 게임의 신규 캐릭터를 확인할까요?",
            color=0x5865F2,
        )
        view = NewContentSelectView(self, ctx, 'character')
        await ctx.send(embed=embed, view=view)

    @commands.command(name="신무기")
    async def new_weapons(self, ctx):
        """신규 무기 — 게임 선택 후 확인"""
        embed = discord.Embed(
            title="🆕 신규 무기 조회",
            description="어떤 게임의 신규 무기를 확인할까요?",
            color=0x5865F2,
        )
        view = NewContentSelectView(self, ctx, 'weapon')
        await ctx.send(embed=embed, view=view)

    # ─── 캐시 초기화 (3게임 통합) ──────────────────────────

    @commands.command(name="갱신", aliases=["캐시초기화"])
    @commands.has_permissions(administrator=True)
    async def refresh_cache(self, ctx):
        """3게임 캐시 전부 초기화 (관리자 전용)"""
        gi = self._get_gi_cog()
        if gi:
            gi._char_cache = {}
            gi._weapon_cache = {}
            gi._artifact_cache = {}
        hsr = self._get_hsr_cog()
        if hsr:
            hsr._char_cache = {}
            hsr._lc_cache = {}
            hsr._relic_cache = {}
        zzz = self._get_zzz_cog()
        if zzz:
            zzz._agent_cache = {}
            zzz._wengine_cache = {}
            zzz._disk_cache = {}
        await ctx.send("✅ 원신/스타레일/젠존제 캐시가 모두 초기화되었습니다.")


# ─── 신규 콘텐츠 게임 선택 View ──────────────────────────

class NewContentSelectView(ui.View):
    """신캐/신무기에서 게임을 선택하는 드롭다운"""
    def __init__(self, cog, ctx, content_type):
        super().__init__(timeout=30)
        self.cog = cog
        self.ctx = ctx
        self.content_type = content_type  # 'character' or 'weapon'

        options = []
        for gk in ['gi', 'hsr', 'zzz']:
            gi = GAME_INFO[gk]
            options.append(discord.SelectOption(
                label=gi['name'], value=gk, emoji=gi['emoji']
            ))
        select = ui.Select(placeholder="게임을 선택하세요", options=options)
        select.callback = self._callback
        self.add_item(select)

    async def interaction_check(self, interaction):
        return interaction.user == self.ctx.author

    async def _callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        game_key = interaction.data['values'][0]

        if game_key == 'gi':
            await self._show_gi_new(interaction)
        elif game_key == 'hsr':
            await self._show_hsr_new(interaction)
        elif game_key == 'zzz':
            await self._show_zzz_new(interaction)

    async def _show_gi_new(self, interaction):
        gi = self.cog._get_gi_cog()
        if not gi:
            await interaction.followup.send("❌ 원신 모듈이 로드되지 않았습니다.", ephemeral=True)
            return

        from utils.honeyhunter import fetch_new_content
        session = await gi._get_session()
        new = await fetch_new_content(session)

        if self.content_type == 'character':
            if not new or not new['characters']:
                await interaction.followup.send("❌ 원신 신규 캐릭터 정보를 불러올 수 없습니다.", ephemeral=True)
                return
            chars = new['characters']
            version = new['version']
            desc = "\n".join(f"• **{c['name']}**" for c in chars)
            embed = discord.Embed(
                title=f"🆕 원신 {version} 신규 캐릭터",
                description=desc + "\n\n아래 버튼을 눌러 상세 정보를 확인하세요.",
                color=GAME_INFO['gi']['color']
            )
            items = [{'name': c['name'], 'slug': c['slug'], 'game': 'gi', 'cat': 'character'} for c in chars]
            view = NewItemButtonView(self.cog, self.ctx, items)
            await interaction.followup.send(embed=embed, view=view)
        else:
            if not new or not new['weapons']:
                await interaction.followup.send("❌ 원신 신규 무기 정보를 불러올 수 없습니다.", ephemeral=True)
                return
            wpns = new['weapons']
            version = new['version']
            desc = "\n".join(f"• **{w['name']}**" for w in wpns)
            embed = discord.Embed(
                title=f"🆕 원신 {version} 신규 무기",
                description=desc + "\n\n아래 버튼을 눌러 상세 정보를 확인하세요.",
                color=GAME_INFO['gi']['color']
            )
            items = [{'name': w['name'], 'slug': w['slug'], 'game': 'gi', 'cat': 'weapon'} for w in wpns]
            view = NewItemButtonView(self.cog, self.ctx, items)
            await interaction.followup.send(embed=embed, view=view)

    async def _show_hsr_new(self, interaction):
        hsr = self.cog._get_hsr_cog()
        if not hsr:
            await interaction.followup.send("❌ 스타레일 모듈이 로드되지 않았습니다.", ephemeral=True)
            return

        if self.content_type == 'character':
            await hsr._ensure_char_cache()
            sorted_items = sorted(hsr._char_cache.items(), key=lambda x: x[1].get('createdAt', ''), reverse=True)[:5]
            desc = "\n".join(f"• **{n}**" for n, _ in sorted_items)
            embed = discord.Embed(
                title="🆕 스타레일 최근 추가 캐릭터",
                description=(desc or "정보 없음") + "\n\n아래 버튼을 눌러 상세 정보를 확인하세요.",
                color=GAME_INFO['hsr']['color']
            )
            items = [{'name': n, 'data': d, 'game': 'hsr', 'cat': 'character'} for n, d in sorted_items]
            view = NewItemButtonView(self.cog, self.ctx, items)
            await interaction.followup.send(embed=embed, view=view)
        else:
            await hsr._ensure_lc_cache()
            sorted_items = sorted(hsr._lc_cache.items(), key=lambda x: x[1].get('createdAt', ''), reverse=True)[:5]
            desc = "\n".join(f"• **{n}**" for n, _ in sorted_items)
            embed = discord.Embed(
                title="🆕 스타레일 최근 추가 광추",
                description=(desc or "정보 없음") + "\n\n아래 버튼을 눌러 상세 정보를 확인하세요.",
                color=GAME_INFO['hsr']['color']
            )
            items = [{'name': n, 'data': d, 'game': 'hsr', 'cat': 'weapon'} for n, d in sorted_items]
            view = NewItemButtonView(self.cog, self.ctx, items)
            await interaction.followup.send(embed=embed, view=view)

    async def _show_zzz_new(self, interaction):
        zzz = self.cog._get_zzz_cog()
        if not zzz:
            await interaction.followup.send("❌ 젠존제 모듈이 로드되지 않았습니다.", ephemeral=True)
            return

        if self.content_type == 'character':
            await zzz._ensure_agent_cache()
            sorted_items = sorted(zzz._agent_cache.items(), key=lambda x: x[1].get('createdAt', ''), reverse=True)[:5]
            desc = "\n".join(f"• **{n}**" for n, _ in sorted_items)
            embed = discord.Embed(
                title="🆕 젠존제 최근 추가 에이전트",
                description=(desc or "정보 없음") + "\n\n아래 버튼을 눌러 상세 정보를 확인하세요.",
                color=GAME_INFO['zzz']['color']
            )
            items = [{'name': n, 'data': d, 'game': 'zzz', 'cat': 'character'} for n, d in sorted_items]
            view = NewItemButtonView(self.cog, self.ctx, items)
            await interaction.followup.send(embed=embed, view=view)
        else:
            await zzz._ensure_wengine_cache()
            sorted_items = sorted(zzz._wengine_cache.items(), key=lambda x: x[1].get('createdAt', ''), reverse=True)[:5]
            desc = "\n".join(f"• **{n}**" for n, _ in sorted_items)
            embed = discord.Embed(
                title="🆕 젠존제 최근 추가 W-엔진",
                description=(desc or "정보 없음") + "\n\n아래 버튼을 눌러 상세 정보를 확인하세요.",
                color=GAME_INFO['zzz']['color']
            )
            items = [{'name': n, 'data': d, 'game': 'zzz', 'cat': 'weapon'} for n, d in sorted_items]
            view = NewItemButtonView(self.cog, self.ctx, items)
            await interaction.followup.send(embed=embed, view=view)


# ─── 신규 항목 버튼 View (목록 → 클릭 → 상세) ───────────

class NewItemButtonView(ui.View):
    """신규 캐릭터/무기 목록에서 각 항목을 버튼으로 표시, 클릭시 상세"""
    def __init__(self, cog, ctx, items):
        super().__init__(timeout=60)
        self.cog = cog
        self.ctx = ctx
        for i, item in enumerate(items[:5]):
            btn = ui.Button(label=item['name'], style=discord.ButtonStyle.primary, custom_id=f"new_{i}")
            btn.callback = self._make_callback(item)
            self.add_item(btn)

    def _make_callback(self, item):
        async def callback(interaction: discord.Interaction):
            await interaction.response.defer()
            game = item['game']
            cat = item['cat']
            name = item['name']

            if game == 'gi':
                gi = self.cog._get_gi_cog()
                if not gi: return
                session = await gi._get_session()
                if cat == 'character':
                    from utils.honeyhunter import fetch_character_detail
                    detail = await fetch_character_detail(session, item['slug'])
                    if not detail:
                        await interaction.followup.send(f"❌ {name} 정보 불러오기 실패", ephemeral=True)
                        return
                    embed, view = gi._build_character_response(detail)
                    embed.title = f"🆕 신규 — {embed.title}"
                    await interaction.followup.send(embed=embed, view=view)
                else:
                    from utils.honeyhunter import fetch_weapon_detail
                    detail = await fetch_weapon_detail(session, item['slug'])
                    if not detail:
                        await interaction.followup.send(f"❌ {name} 정보 불러오기 실패", ephemeral=True)
                        return
                    embed = gi._build_weapon_embed(detail)
                    embed.title = f"🆕 신규 — {embed.title}"
                    await interaction.followup.send(embed=embed)

            elif game == 'hsr':
                hsr = self.cog._get_hsr_cog()
                if not hsr: return
                data = item['data']
                if cat == 'character':
                    session = await hsr._get_session()
                    from utils.prydwen_hsr import fetch_character_detail
                    detail = await fetch_character_detail(session, data['slug'])
                    if not detail:
                        await interaction.followup.send(f"❌ {name} 정보 불러오기 실패", ephemeral=True)
                        return
                    embed, view = hsr._build_character_response(detail)
                    embed.title = f"🆕 신규 — {embed.title}"
                    await interaction.followup.send(embed=embed, view=view)
                else:
                    embed = hsr._build_lightcone_embed(name, data)
                    embed.title = f"🆕 신규 — {embed.title}"
                    await interaction.followup.send(embed=embed)

            elif game == 'zzz':
                zzz = self.cog._get_zzz_cog()
                if not zzz: return
                data = item['data']
                if cat == 'character':
                    session = await zzz._get_session()
                    from utils.prydwen_zzz import fetch_agent_detail
                    detail = await fetch_agent_detail(session, data['slug'])
                    if not detail:
                        await interaction.followup.send(f"❌ {name} 정보 불러오기 실패", ephemeral=True)
                        return
                    embed, view = zzz._build_agent_response(detail)
                    embed.title = f"🆕 신규 — {embed.title}"
                    await interaction.followup.send(embed=embed, view=view)
                else:
                    from utils.prydwen_zzz import ELEMENT_KO
                    color_map = {'S': 0xE8A63C, 'A': 0xA66BBD, 'B': 0x5C92C2}
                    color = color_map.get(data.get('rarity', 'A'), 0x808080)
                    embed = discord.Embed(title=f"🆕 신규 — 【{data.get('rarity','A')}】 {name}", color=color)
                    info = f"⚡ 속성: **{ELEMENT_KO.get(data.get('element',''), data.get('element',''))}**\n"
                    info += f"🎯 타입: **{data.get('type_ko', data.get('type', ''))}**"
                    embed.add_field(name="기본 정보", value=info, inline=False)
                    if data.get('talent_name'):
                        txt = f"**{data['talent_name']}**"
                        if data.get('description'):
                            txt += f"\n{data['description'][:500]}"
                        embed.add_field(name="🔮 W-엔진 효과", value=txt[:1024], inline=False)
                    embed.set_footer(text="데이터: Prydwen.gg")
                    await interaction.followup.send(embed=embed)

        return callback

    async def interaction_check(self, interaction):
        return interaction.user == self.ctx.author


async def setup(bot):
    await bot.add_cog(HoyoInfo(bot))
