import discord
from discord import app_commands
from discord.ext import commands
import random
from datetime import date
from utils.config import CHARACTER_FORTUNES
from utils.data import load_data, save_data

class Fortune(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="뽑기", description="오늘의 운세를 확인해요 (하루 1회)")
    async def slash_fortune(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        today = date.today().isoformat()
        
        data = load_data()
        
        # fortune_dates가 없을 경우를 대비해 안전하게 처리
        if "fortune_dates" not in data:
            data["fortune_dates"] = {}
        
        if data["fortune_dates"].get(user_id) == today:
            embed = discord.Embed(
                title="오늘의 운세는 이미 확인했어요!",
                description="내일 다시 확인해주세요~",
                color=0x808080
            )
            await interaction.response.send_message(embed=embed)
            return
        
        # weights = [0.5 if char[0] == "삼칠이" else 1.0 for char in CHARACTER_FORTUNES]
        character, emoji, description, color = random.choice(CHARACTER_FORTUNES)
        
        data["fortune_dates"][user_id] = today
        save_data(data)
        
        embed = discord.Embed(
            title=f"{emoji} 오늘의 운세: {character}",
            description=description,
            color=color
        )
        embed.set_footer(text=f"요청자: {interaction.user.display_name}")
        await interaction.response.send_message(embed=embed)
    
    @commands.command(name="뽑기")
    async def fortune(self, ctx):
        user_id = str(ctx.author.id)
        today = date.today().isoformat()
        
        data = load_data()
        
        # fortune_dates가 없을 경우를 대비해 안전하게 처리
        if "fortune_dates" not in data:
            data["fortune_dates"] = {}
        
        if data["fortune_dates"].get(user_id) == today:
            embed = discord.Embed(
                title="오늘의 운세는 이미 확인했어요!",
                description="내일 다시 확인해주세요~",
                color=0x808080
            )
            await ctx.send(embed=embed)
            return
        
        # weights = [0.5 if char[0] == "삼칠이" else 1.0 for char in CHARACTER_FORTUNES]
        character, emoji, description, color = random.choice(CHARACTER_FORTUNES)
        
        data["fortune_dates"][user_id] = today
        save_data(data)
        
        embed = discord.Embed(
            title=f"{emoji} 오늘의 운세: {character}",
            description=description,
            color=color
        )
        embed.set_footer(text=f"요청자: {ctx.author.display_name}")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Fortune(bot))
