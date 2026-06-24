import discord
from discord.ext import commands, tasks
import aiohttp
import asyncio
from datetime import datetime
from xml.etree import ElementTree
from utils.config import YOUTUBE_CHANNELS
from utils.data import load_sent_videos, save_sent_videos, get_channels_for_type
from cogs.settings import get_guild_settings

sent_videos = load_sent_videos()

FIXED_MINUTES = [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55]

async def get_videos_via_rss(channel_id, max_results=5):
    rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(rss_url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                if resp.status != 200:
                    print(f"[RSS] 실패: {resp.status}")
                    return []
                xml_text = await resp.text()
        
        root = ElementTree.fromstring(xml_text)
        ns = {"atom": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015", "media": "http://search.yahoo.com/mrss/"}
        
        videos = []
        for entry in root.findall("atom:entry", ns)[:max_results]:
            video_id = entry.find("yt:videoId", ns)
            title = entry.find("atom:title", ns)
            published = entry.find("atom:published", ns)
            
            if video_id is not None:
                thumbnail_url = f"https://i.ytimg.com/vi/{video_id.text}/hqdefault.jpg"
                videos.append({
                    "video_id": video_id.text,
                    "title": title.text if title is not None else "제목 없음",
                    "thumbnail": thumbnail_url,
                    "published_at": published.text if published is not None else ""
                })
        return videos
    except Exception as e:
        print(f"[RSS] 오류: {e}")
        return []

async def get_latest_videos(channel_id, max_results=5):
    # RSS 모드 강제 사용 (API 비활성화)
    return await get_videos_via_rss(channel_id, max_results)

class YouTube(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_youtube.start()
    
    def cog_unload(self):
        self.check_youtube.cancel()
    
    @commands.command(name="영상확인", aliases=["RSS테스트"])
    @commands.has_permissions(administrator=True)
    async def rss_test(self, ctx, channel: str = "genshin"):
        channel_map = {
            "원신": "genshin_yt",
            "genshin": "genshin_yt",
            "스타레일": "starrail_yt",
            "starrail": "starrail_yt",
            "젠레스": "zzz_yt",
            "zzz": "zzz_yt",
            "명조": "wuwa_yt",
            "wuwa": "wuwa_yt",
            "쁘띠플레닛": "petitplanet_yt",
            "쁘띠": "petitplanet_yt",
            "petit": "petitplanet_yt",
            "varsapura": "varsapura_yt",
            "바르사푸라": "varsapura_yt",
            "넥서스아니마": "nexusanima_yt",
            "넥서스": "nexusanima_yt",
            "nexus": "nexusanima_yt",
            "nexus": "nexusanima_yt",
            "엔드필드": "endfield_yt",
            "endfield": "endfield_yt",
        }
        
        yt_key = channel_map.get(channel.lower())
        
        if not yt_key:
            available = ", ".join(set(channel_map.keys()))
            await ctx.send(f"❌ 채널을 찾을 수 없어요!\n가능한 채널: {available}")
            return
        
        if yt_key not in YOUTUBE_CHANNELS:
            await ctx.send("❌ 설정(config)에 없는 채널이에요!")
            return
        
        yt_info = YOUTUBE_CHANNELS[yt_key]
        
        async with ctx.typing():
            videos = await get_videos_via_rss(yt_info["channel_id"], max_results=1)
        
        if not videos:
            await ctx.send("❌ RSS에서 영상을 가져올 수 없어요!")
            return
        
        video = videos[0]
        url = f"https://www.youtube.com/watch?v={video['video_id']}"
        
        await ctx.send(f"🧪 **[RSS 테스트] {yt_info['name']}** 새 영상!\n{url}")
    
    async def send_youtube_notification(self, video, yt_channel_key):
        global sent_videos
        video_id = video["video_id"]
        
        if video_id in sent_videos:
            return False
        
        url = f"https://www.youtube.com/watch?v={video_id}"
        yt_info = YOUTUBE_CHANNELS[yt_channel_key]
        guild_settings = get_guild_settings()
        
        discord_channels = get_channels_for_type(guild_settings, yt_channel_key)
        if not discord_channels:
            return False
        
        for channel_id in discord_channels:
            channel = self.bot.get_channel(channel_id)
            if channel:
                await channel.send(f"{yt_info['emoji']} **{yt_info['name']}** 새 영상!\n{url}")
        
        sent_videos.add(video_id)
        save_sent_videos(sent_videos)
        return True
    
    @tasks.loop(minutes=1)
    async def check_youtube(self):
        global sent_videos
        
        current_minute = datetime.now().minute
        if current_minute not in FIXED_MINUTES:
            return
        
        print(f"[유튜브] 체크 중... ({current_minute}분, RSS 모드)")
        guild_settings = get_guild_settings()
        
        for yt_key, yt_info in YOUTUBE_CHANNELS.items():
            registered_channels = get_channels_for_type(guild_settings, yt_key)
            if not registered_channels:
                continue
            
            videos = await get_latest_videos(yt_info["channel_id"], max_results=5)
            
            for video in reversed(videos):
                video_id = video["video_id"]
                
                if video_id in sent_videos:
                    continue
                
                await self.send_youtube_notification(video, yt_key)
            
            await asyncio.sleep(1)
    
    @check_youtube.before_loop
    async def before_check_youtube(self):
        global sent_videos
        await self.bot.wait_until_ready()
        
        print("[유튜브] 기존 영상 캐싱 중... (RSS 모드)")
        
        for yt_key, yt_info in YOUTUBE_CHANNELS.items():
            videos = await get_latest_videos(yt_info["channel_id"], max_results=5)
            for video in videos:
                sent_videos.add(video["video_id"])
            await asyncio.sleep(0.5)
        
        save_sent_videos(sent_videos)
        print(f"[유튜브] 초기화 완료. 기존 영상 {len(sent_videos)}개 캐시됨. 이후 새 영상만 알림됩니다.")

async def setup(bot):
    await bot.add_cog(YouTube(bot))
