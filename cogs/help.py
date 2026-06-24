import discord
from discord import app_commands
from discord.ext import commands


def build_help_embed(is_admin: bool) -> discord.Embed:
    """도움말 embed 생성. 관리자에게만 관리/진단·알림설정 섹션을 보여준다."""
    embed = discord.Embed(
        title="📜 명령어 목록",
        description="아래 명령어를 쓸 수 있어요! (`/` 슬래시 또는 `!` 둘 다 가능)",
        color=0x9966CC,
    )
    embed.add_field(
        name="🔮 운세 · 기원",
        value="`!운세` — 오늘의 운세 (하루 1회)\n"
              "`!기원` · `!기원 10` · `!기원 100` — 기원 시뮬 (1~100회)\n"
              "`!기원리셋` — 누적 기록 초기화",
        inline=False,
    )
    embed.add_field(
        name="💬 캐릭터 대화",
        value="`!푸리나` · `!콜롬비나` · `!캐서린` + 할 말\n"
              "예: `!푸리나 안녕`   ·   리셋: `!푸리나리셋`",
        inline=False,
    )
    embed.add_field(
        name="🔍 정보 조회",
        value="`!캐릭터 이름` · `!무기 이름` · `!성유물 이름`\n"
              "원신 · 스타레일 · 젠레스 통합 검색",
        inline=False,
    )
    embed.add_field(
        name="🆕 출시 예정",
        value="`!신캐` · `!신무기` · `!신성유물`",
        inline=False,
    )
    embed.add_field(
        name="🎮 빌드 · 이벤트",
        value="`!uid 숫자` — UID 등록   ·   `!빌드 캐릭터` — 빌드 조회\n"
              "`!이벤트 게임명` — 진행 중 이벤트",
        inline=False,
    )

    if is_admin:
        embed.add_field(
            name="📬 알림 설정 (관리자)",
            value="`!알림설정` · `!알림해제` · `!알림현황`",
            inline=False,
        )
        embed.add_field(
            name="🔧 관리 · 진단 (관리자)",
            value="`!업데이트상태` — nanoka 업데이트 상태\n"
                  "`!커뮤확인 게임명` — 커뮤니티 최근 글\n"
                  "`!영상확인 게임명` — 유튜브 최근 영상",
            inline=False,
        )

    embed.set_footer(text="슬래시 명령어(/)도 사용 가능해요")
    return embed


class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    def _is_admin(user) -> bool:
        perms = getattr(user, "guild_permissions", None)
        return bool(perms and perms.administrator)

    @app_commands.command(name="도움", description="명령어 목록을 확인합니다.")
    async def slash_help(self, interaction: discord.Interaction):
        embed = build_help_embed(self._is_admin(interaction.user))
        await interaction.response.send_message(embed=embed)

    @commands.command(name="도움")
    async def help_command(self, ctx):
        embed = build_help_embed(self._is_admin(ctx.author))
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Help(bot))
