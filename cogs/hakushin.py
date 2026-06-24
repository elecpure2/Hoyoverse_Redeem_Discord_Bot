import discord
from discord.ext import commands, tasks
from discord import app_commands
import aiohttp
import hashlib
import json
import os
from utils.config import SENT_HAKUSHIN_FILE
from utils.data import load_guild_settings
from utils import nanoka

# 표시용 게임 메타데이터. 데이터 자체는 nanoka manifest.json 한 방으로 가져온다.
GAME_CONFIGS = {
    "gi": {"name": "원신", "color": 0xFFD700, "emoji": "🌟"},
    "hsr": {"name": "스타레일", "color": 0x87CEEB, "emoji": "🚂"},
    "zzz": {"name": "젠레스 존 제로", "color": 0xFF6B6B, "emoji": "📺"},
}


def _hash_new(new_block: dict) -> str:
    """게임별 new 블록(신규 ID 목록)을 해시로 변환."""
    return hashlib.md5(json.dumps(new_block, sort_keys=True).encode()).hexdigest()


class HakushinNotify(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cache = self._load_cache()
        self.check_updates.start()

    def cog_unload(self):
        self.check_updates.cancel()

    def _load_cache(self) -> dict:
        """저장된 해시 캐시 로드"""
        if os.path.exists(SENT_HAKUSHIN_FILE):
            try:
                with open(SENT_HAKUSHIN_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if "hashes" not in data:
                        return {"hashes": {"gi": "", "hsr": "", "zzz": ""}}
                    return data
            except Exception:
                pass
        return {"hashes": {"gi": "", "hsr": "", "zzz": ""}}

    def _save_cache(self):
        with open(SENT_HAKUSHIN_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.cache, f, ensure_ascii=False, indent=2)

    async def _fetch_new_block(self, session, game_key: str) -> tuple[dict | None, str]:
        """manifest 에서 해당 게임의 new 블록과 그 해시를 반환."""
        manifest = await nanoka.fetch_manifest(session)
        if not manifest:
            return None, ""
        new_block = manifest.get(game_key, {}).get("new")
        if new_block is None:
            return None, ""
        return new_block, _hash_new(new_block)

    @tasks.loop(minutes=30)
    async def check_updates(self):
        print("[Nanoka] 업데이트 확인 중...")
        # manifest 는 fetch_manifest 내부에서 캐싱되므로 1회만 실제 요청됨
        async with aiohttp.ClientSession() as session:
            # 매 루프마다 최신 manifest 를 강제로 한 번 받아온다
            await nanoka.fetch_manifest(session, force=True)

            for game_key, config in GAME_CONFIGS.items():
                try:
                    new_block, new_hash = await self._fetch_new_block(session, game_key)
                    if new_block is None:
                        continue

                    old_hash = self.cache["hashes"].get(game_key, "")

                    if new_hash != old_hash and old_hash != "":
                        print(f"[Nanoka] {config['name']} 업데이트 감지! ({old_hash[:8]} → {new_hash[:8]})")
                        await self._send_notification(game_key, config, new_block)

                    self.cache["hashes"][game_key] = new_hash
                except Exception as e:
                    print(f"[Nanoka] {config['name']} 확인 실패: {e}")

        self._save_cache()
        print("[Nanoka] 업데이트 확인 완료")

    @check_updates.before_loop
    async def before_check_updates(self):
        await self.bot.wait_until_ready()

        # 초기 해시 로드 (처음이면 현재 해시 저장 → 봇 시작 직후 알림 폭탄 방지)
        if not any(self.cache["hashes"].values()):
            print("[Nanoka] 초기 해시 로딩 중...")
            async with aiohttp.ClientSession() as session:
                for game_key in GAME_CONFIGS:
                    _, new_hash = await self._fetch_new_block(session, game_key)
                    if new_hash:
                        self.cache["hashes"][game_key] = new_hash
                        print(f"[Nanoka] {GAME_CONFIGS[game_key]['name']}: {new_hash[:8]}")
            self._save_cache()
            print("[Nanoka] 초기 해시 로딩 완료")

    async def _send_notification(self, game_key: str, config: dict, new_block: dict):
        """업데이트 알림 전송"""
        guild_settings = load_guild_settings()
        site = nanoka.site_url(game_key)

        embed = discord.Embed(
            title=f"🆕 {config['name']} 데이터 업데이트!",
            description="nanoka.cc에 새로운 데이터가 추가되었어요!",
            color=config["color"],
            url=site,
        )

        new_chars = new_block.get(nanoka.NEW_CHAR_KEY, [])
        new_weapons = new_block.get(nanoka.WEAPON_ENDPOINT[game_key], [])
        new_artifacts = new_block.get(nanoka.NEW_ARTIFACT_KEY[game_key], [])

        if new_chars:
            embed.add_field(
                name="👤 신규 캐릭터",
                value=f"ID: {', '.join(map(str, new_chars[:5]))}{'...' if len(new_chars) > 5 else ''}",
                inline=False,
            )

        if new_weapons:
            weapon_label = "광추" if game_key == "hsr" else ("음동기" if game_key == "zzz" else "무기")
            embed.add_field(
                name=f"⚔️ 신규 {weapon_label}",
                value=f"ID: {', '.join(map(str, new_weapons[:5]))}{'...' if len(new_weapons) > 5 else ''}",
                inline=False,
            )

        if new_artifacts:
            art_label = "유물" if game_key == "hsr" else ("디스크" if game_key == "zzz" else "성유물")
            embed.add_field(
                name=f"💎 신규 {art_label}",
                value=f"ID: {', '.join(map(str, new_artifacts[:5]))}{'...' if len(new_artifacts) > 5 else ''}",
                inline=False,
            )

        embed.add_field(
            name="🔗 자세히 보기",
            value=f"[nanoka.cc에서 확인하기]({site})",
            inline=False,
        )

        embed.set_footer(text="nanoka.cc 데이터 기반 • 30분마다 체크")

        sent_count = 0
        for guild_id, settings in guild_settings.items():
            channel_id = settings.get("hakushin_update")
            if channel_id:
                try:
                    channel = self.bot.get_channel(int(channel_id))
                    if channel:
                        await channel.send(embed=embed)
                        sent_count += 1
                except Exception as e:
                    print(f"[Nanoka] 알림 전송 실패 (guild {guild_id}): {e}")

        print(f"[Nanoka] {config['name']} 알림 {sent_count}개 채널에 전송")

    async def _build_status_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="📊 Nanoka 상태",
            description="현재 저장된 해시와 최신 해시를 비교합니다.",
            color=0x5865F2,
        )
        async with aiohttp.ClientSession() as session:
            await nanoka.fetch_manifest(session, force=True)
            for game_key, config in GAME_CONFIGS.items():
                saved_hash = (self.cache["hashes"].get(game_key) or "없음")[:8]
                _, current_hash = await self._fetch_new_block(session, game_key)
                current_hash = current_hash[:8] if current_hash else "오류"
                status = "✅ 동일" if saved_hash == current_hash else "🔄 변경됨"
                embed.add_field(
                    name=f"{config['emoji']} {config['name']}",
                    value=f"저장: `{saved_hash}`\n현재: `{current_hash}`\n상태: {status}",
                    inline=True,
                )
        embed.set_footer(text="30분마다 자동 체크됩니다")
        return embed

    @app_commands.command(name="업데이트상태", description="nanoka 업데이트 알림 상태를 확인해요 (관리자 전용)")
    @app_commands.default_permissions(administrator=True)
    async def slash_hakushin_test(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed = await self._build_status_embed()
        await interaction.followup.send(embed=embed)

    @commands.command(name="업데이트상태", aliases=["하쿠신테스트"])
    @commands.has_permissions(administrator=True)
    async def hakushin_test(self, ctx):
        """nanoka 업데이트 상태 확인"""
        embed = await self._build_status_embed()
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(HakushinNotify(bot))
