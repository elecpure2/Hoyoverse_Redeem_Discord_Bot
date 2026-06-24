import discord
from discord.ext import commands
from discord import app_commands
import re
import aiohttp
from cogs.hoyo_shared import Game, GAME_COLORS, GAME_URLS, clean_description, HoyoSelectView, GameSelectView
from utils import nanoka


class HoyoArtifacts(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._artifact_cache_gi = {}
        self._artifact_cache_hsr = {}
        self._artifact_cache_zzz = {}

    def _get_artifact_term(self, game: Game) -> str:
        if game == Game.HSR:
            return "유물/장신구"
        if game == Game.ZZZ:
            return "디스크"
        return "성유물"

    def _format_hsr_desc(self, desc: str, params: list) -> str:
        """스타레일 세트 설명의 placeholder(#1[i]% 등)를 실제 값으로 치환."""
        if not desc:
            return ""
        desc = re.sub(r'<[^>]+>', '', desc)

        def replace_placeholder(match):
            idx = int(match.group(1)) - 1
            fmt = match.group(2)
            suffix = match.group(3) or ''
            if params and 0 <= idx < len(params):
                val = params[idx]
                if suffix == '%' and isinstance(val, (int, float)):
                    val = val * 100
                if fmt == 'i':
                    return f"{int(val)}{suffix}"
                if fmt.startswith('f'):
                    decimals = int(fmt[1]) if len(fmt) > 1 else 1
                    return f"{val:.{decimals}f}{suffix}"
                return f"{val}{suffix}"
            return match.group(0)

        return re.sub(r'#(\d+)\[([^\]]+)\](%?)', replace_placeholder, desc)

    @staticmethod
    def _gi_set_name(art_data: dict) -> str | None:
        set_data = art_data.get('set', {})
        first = next(iter(set_data.values()), {})
        nm = first.get('name', {})
        return nm.get('ko') or nm.get('en')

    async def _load_all_artifact_caches(self):
        targets = [
            ("gi", self._artifact_cache_gi),
            ("hsr", self._artifact_cache_hsr),
            ("zzz", self._artifact_cache_zzz),
        ]
        async with aiohttp.ClientSession() as session:
            for game_key, cache in targets:
                if cache:
                    continue
                try:
                    version = await nanoka.get_version(session, game_key)
                    if not version:
                        continue
                    async with session.get(nanoka.artifact_list_url(game_key, version)) as resp:
                        if resp.status != 200:
                            continue
                        data = await resp.json()
                    if not isinstance(data, dict):
                        continue
                    for art_id, art_data in data.items():
                        if not isinstance(art_data, dict):
                            continue
                        name = None
                        if game_key == "gi":
                            name = self._gi_set_name(art_data)
                        elif game_key == "hsr":
                            name = art_data.get('ko') or art_data.get('en')
                        elif game_key == "zzz":
                            ko = art_data.get('ko', {})
                            name = ko.get('name') if isinstance(ko, dict) else None
                        if name:
                            cache[name.lower()] = str(art_id)
                except Exception as e:
                    print(f"[{game_key}] 성유물 캐시 로드 실패: {e}")

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

    def _extract_set_effects(self, game: Game, art_data: dict, fallback_name: str | None):
        """게임별로 (이름, 2세트효과, 4세트효과, 아이콘url) 추출."""
        name = fallback_name
        set_2pc = set_4pc = None
        icon_url = None
        game_key = GAME_URLS.get(game, "gi")

        if game == Game.GI:
            set_items = list(art_data.get('set', {}).values())
            if set_items:
                first = set_items[0]
                if not name:
                    nm = first.get('name', {})
                    name = nm.get('ko') or nm.get('en')
                dsc = first.get('desc', {})
                set_2pc = dsc.get('ko') or dsc.get('en')
            if len(set_items) >= 2:
                dsc = set_items[1].get('desc', {})
                set_4pc = dsc.get('ko') or dsc.get('en')
            icon_url = nanoka.artifact_icon_url("gi", art_data.get('icon'))

        elif game == Game.HSR:
            if not name:
                name = art_data.get('ko') or art_data.get('en')
            set_data = art_data.get('set', {})
            if '2' in set_data:
                s = set_data['2']
                set_2pc = self._format_hsr_desc(s.get('ko') or s.get('en', ''), s.get('ParamList', []))
            if '4' in set_data:
                s = set_data['4']
                set_4pc = self._format_hsr_desc(s.get('ko') or s.get('en', ''), s.get('ParamList', []))
            icon_url = nanoka.artifact_icon_url("hsr", art_data.get('icon'))

        elif game == Game.ZZZ:
            ko = art_data.get('ko', {})
            if isinstance(ko, dict):
                if not name:
                    name = ko.get('name')
                set_2pc = clean_description(ko.get('desc2', ''))
                set_4pc = clean_description(ko.get('desc4', ''))
            icon_url = nanoka.artifact_icon_url("zzz", art_data.get('icon'))

        return name, set_2pc, set_4pc, icon_url

    async def _show_artifact_detail_by_id(self, interaction, artifact_id, game: Game, game_name: str, artifact_name: str = None):
        artifact_term = self._get_artifact_term(game)
        color = GAME_COLORS.get(game, 0x9370DB)
        game_key = GAME_URLS.get(game, "gi")

        async def send_msg(**kwargs):
            await interaction.followup.send(**kwargs)

        try:
            async with aiohttp.ClientSession() as session:
                version = await nanoka.get_version(session, game_key)
                if not version:
                    await send_msg(content=f"❌ {artifact_term} 정보를 가져올 수 없어요. (버전 조회 실패)")
                    return
                async with session.get(nanoka.artifact_list_url(game_key, version)) as resp:
                    if resp.status != 200:
                        await send_msg(content=f"❌ {artifact_term} 정보를 가져올 수 없어요.")
                        return
                    all_data = await resp.json()

            art_data = all_data.get(str(artifact_id))
            if not art_data:
                await send_msg(content=f"❌ {artifact_term}을 찾을 수 없어요.")
                return

            name, set_2pc, set_4pc, icon_url = self._extract_set_effects(game, art_data, artifact_name)
            if not name:
                name = f"세트 #{artifact_id}"
            elif name.islower():
                name = name.title()

            site = nanoka.site_url(game_key)
            detail_link = f"{site}{nanoka.ARTIFACT_ENDPOINT[game_key]}/{artifact_id}"

            desc_parts = [f"[상세 정보 보기]({detail_link})"]
            if set_2pc or set_4pc:
                desc_parts.append("")
                if set_2pc:
                    desc_parts.append(f"**2세트 효과**\n{set_2pc}")
                if set_4pc:
                    desc_parts.append(f"\n**4세트 효과**\n{set_4pc}")

            embed = discord.Embed(
                title=f"🏺 {name}",
                description="\n".join(desc_parts)[:4096],
                color=color,
            )
            if icon_url:
                embed.set_thumbnail(url=icon_url)
            embed.set_footer(text=f"데이터 출처: nanoka.cc | {game_name}")
            await send_msg(embed=embed)

        except Exception as e:
            print(f"[성유물] 오류: {e}")
            await send_msg(content=f"❌ 정보를 불러오는데 실패했어요: {e}")

    async def _show_new_artifacts(self, interaction: discord.Interaction, game: Game, game_name: str):
        game_key = GAME_URLS.get(game, "gi")
        try:
            async with aiohttp.ClientSession() as session:
                manifest = await nanoka.fetch_manifest(session)
                if not manifest:
                    await interaction.followup.send("❌ 신규 데이터를 가져올 수 없어요.")
                    return
                game_block = manifest.get(game_key, {})
                version = game_block.get("latest")
                artifact_ids = game_block.get("new", {}).get(nanoka.ARTIFACT_ENDPOINT[game_key], [])

                if not artifact_ids:
                    await interaction.followup.send(f"❌ {game_name} 출시 예정 {self._get_artifact_term(game)}이 없어요.")
                    return

                async with session.get(nanoka.artifact_list_url(game_key, version)) as resp:
                    if resp.status != 200:
                        await interaction.followup.send("❌ 성유물 목록을 가져올 수 없어요.")
                        return
                    all_data = await resp.json()

            from types import SimpleNamespace
            artifacts = []
            for aid in artifact_ids[:6]:
                art_data = all_data.get(str(aid))
                if not art_data:
                    continue
                name, _, _, _ = self._extract_set_effects(game, art_data, None)
                a = SimpleNamespace()
                a.id = aid
                a.name = name or f"세트 #{aid}"
                artifacts.append(a)

            if not artifacts:
                await interaction.followup.send(f"❌ {game_name} 출시 예정 정보를 불러올 수 없어요.")
                return

            color = GAME_COLORS.get(game, 0x9370DB)
            artifact_term = self._get_artifact_term(game)
            embed = discord.Embed(
                title=f"🏺 {game_name} · 출시 예정 {artifact_term}",
                description=f"버전 {version or '?'} · 총 {len(artifact_ids)}개 · 아래 버튼으로 상세 정보를 확인하세요",
                color=color,
            )
            for i, art in enumerate(artifacts):
                embed.add_field(name=f"{i+1}.  {art.name}", value="세트 효과는 버튼을 눌러 확인", inline=False)
            embed.set_footer(text="데이터 출처 · nanoka.cc")

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
            for r in results:
                embed.add_field(name=r["game_name"], value=r["name"], inline=True)
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
                    if 'embed' in kwargs:
                        await msg.edit(content=None, embed=kwargs['embed'])
                    elif 'content' in kwargs:
                        await msg.edit(content=kwargs['content'])

            await self._show_artifact_detail_by_id(FakeInteraction(ctx.channel), r["id"], r["game"], r["game_name"], r["name"])
        else:
            view = HoyoSelectView(self, results, results[0]["game"], results[0]["game_name"], 'artifact')
            await msg.edit(content=None, view=view)
            view.message = msg


async def setup(bot):
    await bot.add_cog(HoyoArtifacts(bot))
