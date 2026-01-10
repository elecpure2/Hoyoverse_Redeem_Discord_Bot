import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import re
from datetime import datetime, timezone, timedelta


class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_configs = {
            "genshin": {
                "list_url": "https://sg-hk4e-api.hoyoverse.com/common/hk4e_global/announcement/api/getAnnList",
                "content_url": "https://sg-hk4e-api.hoyoverse.com/common/hk4e_global/announcement/api/getAnnContent",
                "params": {
                    "game": "hk4e",
                    "game_biz": "hk4e_global",
                    "lang": "ko-kr",
                    "bundle_id": "hk4e_global",
                    "level": "60",
                    "platform": "pc",
                    "region": "os_asia",
                    "uid": "800000000"
                },
                "name": "원신",
                "color": 0xFFD700,
                "emoji": "🌟"
            },
            "hsr": {
                "list_url": "https://sg-hkrpg-api.hoyoverse.com/common/hkrpg_global/announcement/api/getAnnList",
                "content_url": "https://sg-hkrpg-api.hoyoverse.com/common/hkrpg_global/announcement/api/getAnnContent",
                "params": {
                    "game": "hkrpg",
                    "game_biz": "hkrpg_global",
                    "lang": "ko-kr",
                    "bundle_id": "hkrpg_global",
                    "level": "70",
                    "platform": "pc",
                    "region": "prod_official_asia",
                    "uid": "800000000"
                },
                "name": "스타레일",
                "color": 0x87CEEB,
                "emoji": "🚂"
            }
        }
    
    async def fetch_events(self, game: str):
        """게임별 이벤트 정보를 가져옵니다."""
        config = self.api_configs.get(game)
        if not config:
            return None
        
        try:
            async with aiohttp.ClientSession() as session:
                # 이벤트 목록 가져오기
                async with session.get(config["list_url"], params=config["params"]) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("retcode") == 0:
                            list_data = data.get("data", {})
                            
                            # 이벤트 상세 내용(보상 정보) 가져오기
                            async with session.get(config["content_url"], params=config["params"]) as content_response:
                                if content_response.status == 200:
                                    content_data = await content_response.json()
                                    if content_data.get("retcode") == 0:
                                        list_data["content_list"] = content_data.get("data", {}).get("list", [])
                            
                            return list_data
        except Exception as e:
            print(f"[이벤트] {game} API 오류: {e}")
        return None
    
    
    def parse_events(self, data: dict, game: str):
        """이벤트 데이터를 파싱합니다."""
        events = []
        now = datetime.now(timezone(timedelta(hours=9)))  # KST
        config = self.api_configs.get(game)
        
        if not data or "list" not in data:
            return events, 0
        
        # content 맵 생성
        content_map = {}
        for item in data.get("content_list", []):
            content_map[item.get("ann_id")] = item.get("content", "")
        
        # 제외할 키워드 (공지/기원/배틀패스 등)
        exclude_keywords = [
            "기원", "기행", "안내", "버전 업데이트", "업데이트 안내", 
            "공지", "알림", "출석", "무명의 공훈", "상점", "스테이지",
            "임무 안내", "최적화", "문제", "발견한", "복구", "HoYoLAB",
            "연장 보상", "기간 및 내용"
        ]
        
        for category in data["list"]:
            type_id = category.get("type_id")
            # type 1 = 이벤트, type 26 = 캐릭터 체험, type 4 = 스타레일 이벤트
            if type_id not in [1, 4, 26]:
                continue
            
            for item in category.get("list", []):
                try:
                    title = item.get("subtitle") or item.get("title", "")
                    
                    # 제외 키워드 체크
                    if any(keyword in title for keyword in exclude_keywords):
                        continue
                    
                    start_str = item.get("start_time", "")
                    end_str = item.get("end_time", "")
                    
                    # 날짜 파싱
                    start_time = datetime.strptime(start_str, "%Y-%m-%d %H:%M:%S")
                    end_time = datetime.strptime(end_str, "%Y-%m-%d %H:%M:%S")
                    
                    # KST로 변환
                    start_time = start_time.replace(tzinfo=timezone(timedelta(hours=8)))
                    end_time = end_time.replace(tzinfo=timezone(timedelta(hours=8)))
                    
                    # 현재 진행 중인 이벤트만
                    if start_time <= now <= end_time:
                        # 영구 이벤트 제외 (종료일이 2029년 이후)
                        if end_time.year >= 2029:
                            continue
                        
                        days_left = (end_time - now).days
                        hours_left = (end_time - now).seconds // 3600
                        
                        # 45일 넘는 이벤트 제외
                        if days_left > 45:
                            continue
                        
                        # 보상 이미지 확인
                        ann_id = item.get("ann_id")
                        content = content_map.get(ann_id, "")
                        has_reward = bool(re.search(r'<img[^>]+src="[^"]+"', content))
                        
                        events.append({
                            "title": title if title else "알 수 없음",
                            "start": start_time.strftime("%m/%d"),
                            "end": end_time.strftime("%m/%d %H:%M"),
                            "days_left": days_left,
                            "hours_left": hours_left,
                            "type": "이벤트" if type_id in [1, 4] else "캐릭터 체험",
                            "has_reward": has_reward
                        })
                except Exception as e:
                    continue
        
        # 남은 일수로 정렬 (마감 임박순)
        events.sort(key=lambda x: (x["days_left"], x["hours_left"]))
        return events
    
    def create_event_embed(self, game: str, events: list):
        """이벤트 임베드를 생성합니다."""
        config = self.api_configs[game]
        
        embed = discord.Embed(
            title=f"{config['emoji']} {config['name']} 진행 중 이벤트",
            color=config["color"],
            timestamp=datetime.now(timezone(timedelta(hours=9)))
        )
        
        if not events:
            embed.description = "현재 진행 중인 이벤트가 없습니다."
            return embed
        
        # 이벤트 목록 생성
        event_lines = []
        for event in events[:15]:  # 최대 15개
            # 남은 기간 표시
            if event["days_left"] > 0:
                time_left = f"{event['days_left']}일"
            else:
                time_left = f"{event['hours_left']}시간"
            
            # 마감 임박 표시
            if event["days_left"] <= 2:
                time_emoji = "🔥"
            else:
                time_emoji = "⏰"
            
            # 보상 표시 (이미지가 있으면 💎 표시)
            reward_text = " 💎" if event.get("has_reward") else ""
            
            line = f"🎮 **{event['title'][:30]}** ({time_emoji} {time_left}){reward_text}"
            event_lines.append(line)
        
        embed.description = "\n".join(event_lines)
        
        embed.set_footer(text=f"총 {len(events)}개 진행 중 • 💎 = 보상 있음")
        
        return embed
    
    @app_commands.command(name="이벤트", description="현재 진행 중인 게임 이벤트를 확인합니다")
    @app_commands.describe(game="이벤트를 확인할 게임")
    @app_commands.choices(game=[
        app_commands.Choice(name="🌟 원신", value="genshin"),
        app_commands.Choice(name="🚂 스타레일", value="hsr"),
    ])
    async def event_command(self, interaction: discord.Interaction, game: str):
        await interaction.response.defer()
        
        data = await self.fetch_events(game)
        if data is None:
            await interaction.followup.send("❌ 이벤트 정보를 가져올 수 없습니다. 잠시 후 다시 시도해주세요.")
            return
        
        events = self.parse_events(data, game)
        embed = self.create_event_embed(game, events)
        
        await interaction.followup.send(embed=embed)
    
    @commands.command(name="이벤트")
    async def event_command_prefix(self, ctx, game: str = None):
        """현재 진행 중인 게임 이벤트를 확인합니다. (원신/스타레일)"""
        game_map = {
            "원신": "genshin",
            "genshin": "genshin",
            "스타레일": "hsr",
            "hsr": "hsr",
            "스레": "hsr",
            "붕스": "hsr"
        }
        
        if not game:
            embed = discord.Embed(
                title="🎮 이벤트 명령어 사용법",
                description="확인할 게임을 선택해주세요!",
                color=0x5865F2
            )
            embed.add_field(
                name="사용법",
                value="`!이벤트 원신`\n`!이벤트 스타레일`",
                inline=False
            )
            await ctx.send(embed=embed)
            return
        
        game_key = game_map.get(game.lower())
        if not game_key:
            await ctx.send("❌ 올바른 게임명을 입력해주세요. (원신/스타레일)")
            return
        
        async with ctx.typing():
            data = await self.fetch_events(game_key)
            if data is None:
                await ctx.send("❌ 이벤트 정보를 가져올 수 없습니다. 잠시 후 다시 시도해주세요.")
                return
            
            events = self.parse_events(data, game_key)
            embed = self.create_event_embed(game_key, events)
            
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Events(bot))

