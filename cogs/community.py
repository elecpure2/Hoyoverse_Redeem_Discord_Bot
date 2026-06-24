import discord
from discord.ext import commands, tasks
import aiohttp
import asyncio
import json
import re
from datetime import datetime
from utils.config import YOUTUBE_CHANNELS
from utils.data import get_channels_for_type
from cogs.settings import get_guild_settings

sent_community_posts = set()
COMMUNITY_CHECK_MINUTES = [2, 7, 12, 17, 22, 27, 32, 37, 42, 47, 52, 57]

def load_sent_community_posts():
    try:
        with open("data/sent_community.json", "r") as f:
            return set(json.load(f))
    except:
        return set()

def save_sent_community_posts():
    global sent_community_posts
    with open("data/sent_community.json", "w") as f:
        json.dump(list(sent_community_posts), f)

async def get_community_posts(channel_id, max_posts=5):
    url = "https://www.youtube.com/youtubei/v1/browse"
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    }
    
    payload = {
        "context": {
            "client": {
                "clientName": "WEB",
                "clientVersion": "2.20241216.00.00",
                "hl": "ko",
                "gl": "KR"
            }
        },
        "browseId": channel_id,
        "params": "Egljb21tdW5pdHnyBgQKAkoA"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                if resp.status != 200:
                    print(f"[커뮤니티] API 실패: {resp.status}")
                    return []
                data = await resp.json()
    except Exception as e:
        print(f"[커뮤니티] 오류: {e}")
        return []
    
    posts = []
    try:
        tabs = data.get("contents", {}).get("twoColumnBrowseResultsRenderer", {}).get("tabs", [])
        
        community_tab = None
        for tab in tabs:
            tab_renderer = tab.get("tabRenderer", {})
            title = tab_renderer.get("title", "")
            if title in ["커뮤니티", "Community", "게시물", "Posts"]:
                community_tab = tab_renderer
                break
        
        if not community_tab:
            # 디버그: 어떤 탭들이 있는지 출력
            tab_names = [tab.get("tabRenderer", {}).get("title", "없음") for tab in tabs]
            print(f"[커뮤니티] 커뮤니티 탭을 찾을 수 없음 (채널: {channel_id}, 탭: {tab_names})")
            return []
        
        content = community_tab.get("content", {})
        section_list = content.get("sectionListRenderer", {})
        contents = section_list.get("contents", [])
        
        for section in contents:
            item_section = section.get("itemSectionRenderer", {})
            items = item_section.get("contents", [])
            
            for item in items[:max_posts]:
                post_renderer = item.get("backstagePostThreadRenderer", {}).get("post", {}).get("backstagePostRenderer", {})
                
                if not post_renderer:
                    continue
                
                post_id = post_renderer.get("postId", "")
                
                content_text = ""
                content_runs = post_renderer.get("contentText", {}).get("runs", [])
                for run in content_runs:
                    content_text += run.get("text", "")
                
                if len(content_text) > 200:
                    content_text = content_text[:200] + "..."
                
                vote_count = post_renderer.get("voteCount", {}).get("simpleText", "0")
                
                published_time = ""
                time_text = post_renderer.get("publishedTimeText", {}).get("runs", [])
                if time_text:
                    published_time = time_text[0].get("text", "")
                
                image_url = None
                backdrop = post_renderer.get("backstageAttachment", {})
                if "backstageImageRenderer" in backdrop:
                    thumbnails = backdrop["backstageImageRenderer"].get("image", {}).get("thumbnails", [])
                    if thumbnails:
                        image_url = thumbnails[-1].get("url", "")
                
                if post_id:
                    posts.append({
                        "post_id": post_id,
                        "content": content_text,
                        "likes": vote_count,
                        "published": published_time,
                        "image_url": image_url,
                        "url": f"https://www.youtube.com/post/{post_id}"
                    })
        
    except Exception as e:
        print(f"[커뮤니티] 파싱 오류: {e}")
        return []
    
    return posts

class Community(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        global sent_community_posts
        sent_community_posts = load_sent_community_posts()
        self.check_community.start()
    
    def cog_unload(self):
        self.check_community.cancel()
    
    @commands.command(name="커뮤확인", aliases=["커뮤테스트"])
    @commands.has_permissions(administrator=True)
    async def community_test(self, ctx, game: str = "genshin"):
        game_map = {
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
        }
        
        yt_key = game_map.get(game.lower(), "genshin_yt")
        
        if yt_key not in YOUTUBE_CHANNELS:
            await ctx.send("❌ 유효하지 않은 게임이에요!")
            return
        
        yt_info = YOUTUBE_CHANNELS[yt_key]
        
        async with ctx.typing():
            posts = await get_community_posts(yt_info["channel_id"], max_posts=1)
        
        if not posts:
            await ctx.send("❌ 커뮤니티 게시물을 가져올 수 없어요!")
            return
        
        post = posts[0]
        
        embed = discord.Embed(
            title=f"🧪 [테스트] {yt_info['name']} 커뮤니티 최신 게시물",
            description=post["content"] if post["content"] else "(이미지/투표 게시물)",
            color=0xFFAA00,
            url=post["url"]
        )
        
        if post["image_url"]:
            embed.set_image(url=post["image_url"])
        
        embed.add_field(name="👍 좋아요", value=post["likes"], inline=True)
        if post["published"]:
            embed.add_field(name="⏰ 게시", value=post["published"], inline=True)
        
        embed.set_footer(text="관리자 진단용 · 커뮤니티 최근 게시물")

        await ctx.send(embed=embed)
    
    @tasks.loop(minutes=1)
    async def check_community(self):
        global sent_community_posts
        
        current_minute = datetime.now().minute
        if current_minute not in COMMUNITY_CHECK_MINUTES:
            return
        
        print(f"[커뮤니티] 체크 중... ({current_minute}분)")
        guild_settings = get_guild_settings()
        
        community_channels = ["genshin_yt", "starrail_yt", "zzz_yt", "wuwa_yt", "petitplanet_yt", "varsapura_yt", "nexusanima_yt"]
        for yt_key in community_channels:
            if yt_key not in YOUTUBE_CHANNELS:
                continue
            yt_info = YOUTUBE_CHANNELS[yt_key]
            community_key = f"{yt_key}_community"
            registered_channels = get_channels_for_type(guild_settings, community_key)
            
            # 커뮤니티 키가 없으면 기본 유튜브 키로 fallback (이전 설정 호환)
            if not registered_channels:
                registered_channels = get_channels_for_type(guild_settings, yt_key)
            
            if not registered_channels:
                # 디버그: 등록된 채널이 없으면 스킵
                continue
            
            print(f"[커뮤니티] {yt_info['name']}: {len(registered_channels)}개 채널에서 알림 대기 중")
            posts = await get_community_posts(yt_info["channel_id"], max_posts=3)
            
            if not posts:
                print(f"[커뮤니티] {yt_info['name']}: 게시물 가져오기 실패")
                continue
            
            new_posts = []
            for post in reversed(posts):
                post_id = post["post_id"]
                
                if post_id in sent_community_posts:
                    continue
                
                print(f"[커뮤니티] 🆕 {yt_info['name']} 새 게시물 발견: {post_id}")
                
                embed = discord.Embed(
                    title=f"📢 {yt_info['name']} 커뮤니티 새 게시물",
                    description=post["content"] if post["content"] else "(이미지/투표 게시물)",
                    color=0xFF0000,
                    url=post["url"]
                )
                
                if post["image_url"]:
                    embed.set_image(url=post["image_url"])
                
                embed.add_field(name="👍 좋아요", value=post["likes"], inline=True)
                if post["published"]:
                    embed.add_field(name="⏰ 게시", value=post["published"], inline=True)
                
                embed.set_footer(text="YouTube 커뮤니티")
                
                for channel_id in registered_channels:
                    channel = self.bot.get_channel(channel_id)
                    if channel:
                        try:
                            await channel.send(embed=embed)
                            print(f"[커뮤니티] ✅ 알림 전송 완료: {channel.name}")
                        except Exception as e:
                            print(f"[커뮤니티] ❌ 메시지 전송 실패 ({channel_id}): {e}")
                    else:
                        print(f"[커뮤니티] ❌ 채널을 찾을 수 없음: {channel_id}")
                
                sent_community_posts.add(post_id)
                new_posts.append(post_id)
            
            # 새 게시물이 있을 때만 한 번 저장 (성능 최적화)
            if new_posts:
                save_sent_community_posts()
                print(f"[커뮤니티] {yt_info['name']}: {len(new_posts)}개 새 게시물 처리 완료")
            
            await asyncio.sleep(2)
    
    @check_community.before_loop
    async def before_check_community(self):
        global sent_community_posts
        await self.bot.wait_until_ready()
        
        print("[커뮤니티] 기존 게시물 캐싱 중...")
        
        community_channels = ["genshin_yt", "starrail_yt", "zzz_yt", "wuwa_yt", "petitplanet_yt", "varsapura_yt", "nexusanima_yt"]
        for yt_key in community_channels:
            if yt_key not in YOUTUBE_CHANNELS:
                continue
            yt_info = YOUTUBE_CHANNELS[yt_key]
            posts = await get_community_posts(yt_info["channel_id"], max_posts=5)
            if posts:
                print(f"[커뮤니티] {yt_info['name']}: {len(posts)}개 캐시")
            for post in posts:
                sent_community_posts.add(post["post_id"])
            await asyncio.sleep(1)
        
        save_sent_community_posts()
        print(f"[커뮤니티] 초기화 완료. 기존 게시물 {len(sent_community_posts)}개 캐시됨.")

async def setup(bot):
    await bot.add_cog(Community(bot))
