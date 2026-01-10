import discord
from discord.ext import commands
import asyncio
import sys
import io
from utils.config import DISCORD_TOKEN

# Windows 콘솔 인코딩 설정 (Cursor 터미널에서는 불필요 - 오히려 출력 차단됨)
# 일반 CMD/PowerShell에서 이모지가 깨질 경우에만 아래 주석 해제
# if sys.platform == 'win32':
#     sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
#     sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

COGS = [
    "cogs.fortune",
    "cogs.gacha",
    "cogs.settings",
    "cogs.redeem",
    "cogs.youtube",
    "cogs.community",
    "cogs.chatbot",
    "cogs.enka",
    "cogs.help",

    # "cogs.upcoming", # Deprecated
    "cogs.hoyo_characters",
    "cogs.hoyo_weapons",
    "cogs.hoyo_artifacts",
    "cogs.hakushin",
    "cogs.events",
]

@bot.event
async def on_ready():
    print(f"✅ {bot.user} 로그인 완료!")
    print(f"📡 {len(bot.guilds)}개 서버에서 활동 중")
    
    try:
        synced = await bot.tree.sync()
        print(f"✅ {len(synced)}개 슬래시 명령어 동기화 완료")
    except Exception as e:
        print(f"❌ 슬래시 명령어 동기화 실패: {e}")

async def load_cogs():
    for cog in COGS:
        try:
            await bot.load_extension(cog)
            print(f"  ✅ {cog} 로드 완료")
        except Exception as e:
            print(f"  ❌ {cog} 로드 실패: {e}")
            # hakushin 관련 모듈은 선택적이므로 경고만 출력
            if 'hakushin' in str(e).lower():
                print(f"  ⚠️ {cog}는 hakushin 모듈이 필요합니다. (선택사항)")

async def main():
    # 토큰 확인
    if not DISCORD_TOKEN:
        print("❌ 오류: DISCORD_TOKEN 환경 변수가 설정되지 않았습니다!")
        print("   PowerShell에서 다음 명령어를 실행하세요:")
        print('   $env:DISCORD_TOKEN="여기에_봇_토큰_입력"')
        return
    
    print("🔄 Cog 로딩 중...")
    await load_cogs()
    
    print("🚀 봇 시작 중...")
    try:
        await bot.start(DISCORD_TOKEN)
    except KeyboardInterrupt:
        print("\n⏹️ 봇 종료 중...")
        await bot.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 봇이 종료되었습니다.")
