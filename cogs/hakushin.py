import discord
from discord.ext import commands, tasks
from discord import app_commands
import aiohttp
import hashlib
import json
import os
from utils.config import SENT_HAKUSHIN_FILE
from utils.data import load_guild_settings

GAME_CONFIGS = {
    "gi": {
        "name": "원신",
        "color": 0xFFD700,
        "emoji": "🌟",
        "api_url": "https://api.hakush.in/gi/new.json",
        "site_url": "https://gi.hakush.in/"
    },
    "hsr": {
        "name": "스타레일",
        "color": 0x87CEEB,
        "emoji": "🚂",
        "api_url": "https://api.hakush.in/hsr/new.json",
        "site_url": "https://hsr.hakush.in/"
    },
    "zzz": {
        "name": "젠레스 존 제로",
        "color": 0xFF6B6B,
        "emoji": "📺",
        "api_url": "https://api.hakush.in/zzz/new.json",
        "site_url": "https://zzz.hakush.in/"
    },
}

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
                    # 새 형식으로 마이그레이션
                    if "hashes" not in data:
                        return {"hashes": {"gi": "", "hsr": "", "zzz": ""}}
                    return data
            except:
                pass
        return {"hashes": {"gi": "", "hsr": "", "zzz": ""}}
    
    def _save_cache(self):
        with open(SENT_HAKUSHIN_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.cache, f, ensure_ascii=False, indent=2)
    
    async def _fetch_new_json(self, game_key: str) -> tuple[dict | None, str]:
        """new.json을 가져오고 해시 반환"""
        config = GAME_CONFIGS[game_key]
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(config["api_url"], timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        content_hash = hashlib.md5(json.dumps(data, sort_keys=True).encode()).hexdigest()
                        return data, content_hash
        except Exception as e:
            print(f"[Hakushin] {config['name']} API 요청 실패: {e}")
        return None, ""
    
    @tasks.loop(minutes=30)
    async def check_updates(self):
        print("[Hakushin] 업데이트 확인 중...")
        
        for game_key, config in GAME_CONFIGS.items():
            try:
                data, new_hash = await self._fetch_new_json(game_key)
                if not data:
                    continue
                
                old_hash = self.cache["hashes"].get(game_key, "")
                
                # 해시가 다르면 = 업데이트 있음!
                if new_hash != old_hash and old_hash != "":
                    print(f"[Hakushin] {config['name']} 업데이트 감지! ({old_hash[:8]} → {new_hash[:8]})")
                    await self._send_notification(game_key, config, data)
                
                # 해시 저장
                self.cache["hashes"][game_key] = new_hash
                
            except Exception as e:
                print(f"[Hakushin] {config['name']} 확인 실패: {e}")
        
        self._save_cache()
        print("[Hakushin] 업데이트 확인 완료")
    
    @check_updates.before_loop
    async def before_check_updates(self):
        await self.bot.wait_until_ready()
        
        # 초기 해시 로드 (처음이면 현재 해시 저장)
        if not any(self.cache["hashes"].values()):
            print("[Hakushin] 초기 해시 로딩 중...")
            for game_key in GAME_CONFIGS:
                _, new_hash = await self._fetch_new_json(game_key)
                if new_hash:
                    self.cache["hashes"][game_key] = new_hash
                    print(f"[Hakushin] {GAME_CONFIGS[game_key]['name']}: {new_hash[:8]}")
            self._save_cache()
            print("[Hakushin] 초기 해시 로딩 완료")
    
    async def _send_notification(self, game_key: str, config: dict, data: dict):
        """업데이트 알림 전송"""
        guild_settings = load_guild_settings()
        
        embed = discord.Embed(
            title=f"🆕 {config['name']} 데이터 업데이트!",
            description=f"hakush.in에 새로운 데이터가 추가되었어요!",
            color=config["color"],
            url=config["site_url"]
        )
        
        # 신규 항목 표시
        new_chars = data.get("character", [])
        new_weapons = data.get("weapon", data.get("lightcone", []))
        new_artifacts = data.get("artifact", data.get("relicset", data.get("equipment", [])))
        
        if new_chars:
            embed.add_field(
                name="👤 신규 캐릭터",
                value=f"ID: {', '.join(map(str, new_chars[:5]))}{'...' if len(new_chars) > 5 else ''}",
                inline=False
            )
        
        if new_weapons:
            weapon_label = "광추" if game_key == "hsr" else ("음동기" if game_key == "zzz" else "무기")
            embed.add_field(
                name=f"⚔️ 신규 {weapon_label}",
                value=f"ID: {', '.join(map(str, new_weapons[:5]))}{'...' if len(new_weapons) > 5 else ''}",
                inline=False
            )
        
        if new_artifacts:
            art_label = "유물" if game_key == "hsr" else ("디스크" if game_key == "zzz" else "성유물")
            embed.add_field(
                name=f"💎 신규 {art_label}",
                value=f"ID: {', '.join(map(str, new_artifacts[:5]))}{'...' if len(new_artifacts) > 5 else ''}",
                inline=False
            )
        
        embed.add_field(
            name="🔗 자세히 보기",
            value=f"[hakush.in에서 확인하기]({config['site_url']})",
            inline=False
        )
        
        embed.set_footer(text="hakush.in 데이터 기반 • 30분마다 체크")
        
        # 알림 전송
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
                    print(f"[Hakushin] 알림 전송 실패 (guild {guild_id}): {e}")
        
        print(f"[Hakushin] {config['name']} 알림 {sent_count}개 채널에 전송")
    
    @app_commands.command(name="하쿠신테스트", description="hakushin 업데이트 알림 테스트 (관리자 전용)")
    @app_commands.default_permissions(administrator=True)
    async def slash_hakushin_test(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        embed = discord.Embed(
            title="📊 Hakushin 상태",
            description="현재 저장된 해시와 최신 해시를 비교합니다.",
            color=0x5865F2
        )
        
        for game_key, config in GAME_CONFIGS.items():
            saved_hash = self.cache["hashes"].get(game_key, "없음")[:8]
            _, current_hash = await self._fetch_new_json(game_key)
            current_hash = current_hash[:8] if current_hash else "오류"
            
            status = "✅ 동일" if saved_hash == current_hash else "🔄 변경됨"
            
            embed.add_field(
                name=f"{config['emoji']} {config['name']}",
                value=f"저장: `{saved_hash}`\n현재: `{current_hash}`\n상태: {status}",
                inline=True
            )
        
        embed.set_footer(text="30분마다 자동 체크됩니다")
        await interaction.followup.send(embed=embed)
    
    @commands.command(name="하쿠신테스트")
    @commands.has_permissions(administrator=True)
    async def hakushin_test(self, ctx):
        """hakushin 업데이트 상태 확인"""
        embed = discord.Embed(
            title="📊 Hakushin 상태",
            description="현재 저장된 해시와 최신 해시를 비교합니다.",
            color=0x5865F2
        )
        
        for game_key, config in GAME_CONFIGS.items():
            saved_hash = self.cache["hashes"].get(game_key, "없음")[:8]
            _, current_hash = await self._fetch_new_json(game_key)
            current_hash = current_hash[:8] if current_hash else "오류"
            
            status = "✅ 동일" if saved_hash == current_hash else "🔄 변경됨"
            
            embed.add_field(
                name=f"{config['emoji']} {config['name']}",
                value=f"저장: `{saved_hash}`\n현재: `{current_hash}`\n상태: {status}",
                inline=True
            )
        
        embed.set_footer(text="30분마다 자동 체크됩니다")
        await ctx.send(embed=embed)
    

async def setup(bot):
    await bot.add_cog(HakushinNotify(bot))
