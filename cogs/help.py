import discord
from discord import app_commands
from discord.ext import commands

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="도움", description="명령어 목록을 확인합니다.")
    async def slash_help(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="📜 명령어 목록",
            description="사용 가능한 명령어들이에요!",
            color=0x9966CC
        )
        embed.add_field(
            name="🔮 !뽑기",
            value="오늘의 운세를 확인해요 (하루 1회)",
            inline=False
        )
        embed.add_field(
            name="💫 기원 (Wish)",
            value="`!기원` - 1회 / `!기원 10` - 10회 / `!기원 100` - 100회\n(1~100회 사이 자유롭게 입력 가능)\n`!기원리셋` - 누적 기록 초기화",
            inline=False
        )
        embed.add_field(
            name="💬 캐릭터 대화",
            value="호요버스 캐릭터들과 대화해요!\n캐릭터: 푸리나, 콜롬비나, 캐서린\n예: `!푸리나 안녕` / 리셋: `!푸리나리셋`",
            inline=False
        )
        embed.add_field(
            name="🎮 Enka 빌드",
            value="`!uid 123456789` - UID 등록\n`!빌드 캐릭터` - 빌드 조회",
            inline=False
        )
        embed.add_field(
            name="🆕 출시 예정 정보",
            value="`!신캐` - 출시 예정 캐릭터\n`!신무기` - 출시 예정 무기/광추\n`!신성유물` - 출시 예정 성유물/유물/디스크",
            inline=False
        )
        embed.add_field(
            name="🔍 상세 정보 조회",
            value="`!캐릭터 이름` - 캐릭터 정보\n`!무기 이름` - 무기/광추 정보\n`!성유물 이름` - 성유물/유물 정보\n`!디스크 이름` - 젠레스 디스크 정보",
            inline=False
        )
        embed.add_field(
            name="🌍 컨텐츠 정보",
            value="`!이벤트 게임명` - 진행 중 이벤트 확인",
            inline=False
        )
        embed.add_field(
            name="📬 알림 설정 (관리자 전용)",
            value="`!알림설정` - 알림 채널 설정\n`!알림해제` - 알림 해제\n`!알림현황` - 현재 설정 확인",
            inline=False
        )
        embed.add_field(
            name="🔧 관리 및 테스트 (관리자 전용)",
            value="`!하쿠신테스트` - 하쿠신 업데이트 상태 확인\n`!커뮤테스트 게임명` - 커뮤니티 최근 글 확인\n`!RSS테스트 게임명` - 유튜브 RSS 최근 영상 확인",
            inline=False
        )
        embed.set_footer(text="슬래시 명령어(/)도 사용 가능해요!")
        await interaction.response.send_message(embed=embed)
    
    @commands.command(name="도움")
    async def help_command(self, ctx):
        embed = discord.Embed(
            title="📜 명령어 목록",
            description="사용 가능한 명령어들이에요!",
            color=0x9966CC
        )
        embed.add_field(
            name="🔮 !뽑기",
            value="오늘의 운세를 확인해요 (하루 1회)",
            inline=False
        )
        embed.add_field(
            name="💫 기원 (Wish)",
            value="`!기원` - 1회 / `!기원 10` - 10회 / `!기원 100` - 100회\n(1~100회 사이 자유롭게 입력 가능)\n`!기원리셋` - 누적 기록 초기화",
            inline=False
        )
        embed.add_field(
            name="💬 캐릭터 대화",
            value="호요버스 캐릭터들과 대화해요!\n캐릭터: 푸리나, 콜롬비나, 캐서린\n예: `!푸리나 안녕` / 리셋: `!푸리나리셋`",
            inline=False
        )
        embed.add_field(
            name="🎮 Enka 빌드",
            value="`!uid 123456789` - UID 등록\n`!빌드 캐릭터` - 빌드 조회",
            inline=False
        )
        embed.add_field(
            name="🆕 출시 예정 정보",
            value="`!신캐` - 출시 예정 캐릭터\n`!신무기` - 출시 예정 무기/광추\n`!신성유물` - 출시 예정 성유물/유물/디스크",
            inline=False
        )
        embed.add_field(
            name="🔍 상세 정보 조회",
            value="`!캐릭터 이름` - 캐릭터 정보\n`!무기 이름` - 무기/광추 정보\n`!성유물 이름` - 성유물/유물 정보\n`!디스크 이름` - 젠레스 디스크 정보",
            inline=False
        )
        embed.add_field(
            name="🌍 컨텐츠 정보",
            value="`!이벤트 게임명` - 진행 중 이벤트 확인",
            inline=False
        )
        embed.add_field(
            name="📬 알림 설정",
            value="`!알림설정` - 알림 채널 설정\n`!알림해제` - 알림 해제\n`!알림현황` - 현재 설정 확인",
            inline=False
        )
        embed.add_field(
            name="🔧 관리 및 테스트 (관리자 전용)",
            value="`!하쿠신테스트` - 하쿠신 업데이트 상태 확인\n`!커뮤테스트 게임명` - 커뮤니티 최근 글 확인\n`!RSS테스트 게임명` - 유튜브 RSS 최근 영상 확인",
            inline=False
        )
        embed.set_footer(text="슬래시 명령어(/)도 사용 가능해요!")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Help(bot))
