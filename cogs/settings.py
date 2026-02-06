import discord
from discord import app_commands
from discord.ext import commands
from utils.config import NOTIFY_TYPES
from utils.data import load_guild_settings, save_guild_settings

guild_settings = load_guild_settings()

def get_guild_settings():
    return guild_settings

class NotifyTypeSelect(discord.ui.Select):
    def __init__(self, channel_id):
        self.channel_id = channel_id
        hidden_types = [
            "genshin_yt_community", "starrail_yt_community", "zzz_yt_community", "wuwa_yt_community",
            "endfield_yt_community", "petitplanet_yt_community", "varsapura_yt_community", "nexusanima_yt_community"
        ]
        options = []
        for key, info in NOTIFY_TYPES.items():
            if key in hidden_types:
                continue
            options.append(discord.SelectOption(
                label=info["name"],
                value=key,
                emoji=info["emoji"]
            ))
        super().__init__(
            placeholder="알림받을 항목을 선택하세요 (여러 개 가능)",
            min_values=1,
            max_values=len(options),
            options=options
        )
    
    async def callback(self, interaction: discord.Interaction):
        global guild_settings
        guild_id = str(interaction.guild.id)
        
        if guild_id not in guild_settings:
            guild_settings[guild_id] = {}
        
        selected = list(self.values)
        added = []
        
        yt_community_pairs = {
            "genshin_yt": "genshin_yt_community",
            "starrail_yt": "starrail_yt_community",
            "zzz_yt": "zzz_yt_community",
            "wuwa_yt": "wuwa_yt_community",
            "petitplanet_yt": "petitplanet_yt_community",
            "varsapura_yt": "varsapura_yt_community",
            "nexusanima_yt": "nexusanima_yt_community",
        }
        
        for notify_type in selected:
            if notify_type in yt_community_pairs:
                community_type = yt_community_pairs[notify_type]
                if community_type not in selected:
                    selected.append(community_type)
        
        for notify_type in selected:
            guild_settings[guild_id][notify_type] = self.channel_id
            if notify_type in NOTIFY_TYPES:
                info = NOTIFY_TYPES[notify_type]
                added.append(f"{info['emoji']} {info['name']}")
        
        save_guild_settings(guild_settings)
        
        embed = discord.Embed(
            title="✅ 알림 설정 완료!",
            description=f"<#{self.channel_id}> 채널에 알림이 설정되었어요!",
            color=0x00FF00
        )
        embed.add_field(name="설정된 알림", value="\n".join(added), inline=False)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

class NotifySelectView(discord.ui.View):
    def __init__(self, channel_id):
        super().__init__(timeout=60)
        self.add_item(NotifyTypeSelect(channel_id))

class RemoveNotifySelect(discord.ui.Select):
    def __init__(self, guild_id, current_settings):
        self.guild_id = guild_id
        options = []
        for key in current_settings:
            if key in NOTIFY_TYPES:
                info = NOTIFY_TYPES[key]
                options.append(discord.SelectOption(
                    label=info["name"],
                    value=key,
                    emoji=info["emoji"]
                ))
        if not options:
            options.append(discord.SelectOption(label="설정된 알림 없음", value="none"))
        super().__init__(
            placeholder="해제할 알림을 선택하세요",
            min_values=1,
            max_values=len(options),
            options=options
        )
    
    async def callback(self, interaction: discord.Interaction):
        global guild_settings
        
        if "none" in self.values:
            await interaction.response.send_message("❌ 설정된 알림이 없어요!", ephemeral=True)
            return
        
        removed = []
        for notify_type in self.values:
            if notify_type in guild_settings.get(self.guild_id, {}):
                del guild_settings[self.guild_id][notify_type]
                info = NOTIFY_TYPES[notify_type]
                removed.append(f"{info['emoji']} {info['name']}")
        
        save_guild_settings(guild_settings)
        
        embed = discord.Embed(
            title="🗑️ 알림 해제 완료!",
            description="\n".join(removed) if removed else "해제된 알림이 없어요",
            color=0xFF6B6B
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

class RemoveNotifyView(discord.ui.View):
    def __init__(self, guild_id, current_settings):
        super().__init__(timeout=60)
        self.add_item(RemoveNotifySelect(guild_id, current_settings))

class Settings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="알림설정", description="이 채널에 알림을 설정해요 (관리자 전용)")
    @app_commands.default_permissions(administrator=True)
    async def slash_notify_setup(self, interaction: discord.Interaction):
        channel_id = interaction.channel.id
        
        embed = discord.Embed(
            title="📬 알림 설정",
            description=f"<#{channel_id}> 채널에 받을 알림을 선택하세요!\n\n**📋 코드 알림**: 리딤코드 자동 알림\n**🎬 유튜브 알림**: 새 영상 알림\n**🆕 신규 업데이트**: hakushin 신캐/무기/성유물 알림",
            color=0x5865F2
        )
        
        view = NotifySelectView(channel_id)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    @app_commands.command(name="알림해제", description="알림 설정을 해제해요 (관리자 전용)")
    @app_commands.default_permissions(administrator=True)
    async def slash_notify_remove(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)
        current = guild_settings.get(guild_id, {})
        
        if not current:
            await interaction.response.send_message("❌ 설정된 알림이 없어요!", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="🗑️ 알림 해제",
            description="해제할 알림을 선택하세요!",
            color=0xFF6B6B
        )
        
        view = RemoveNotifyView(guild_id, current)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    @app_commands.command(name="알림현황", description="현재 알림 설정을 확인해요")
    async def slash_notify_status(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)
        
        if guild_id not in guild_settings or not guild_settings[guild_id]:
            await interaction.response.send_message("📭 설정된 알림이 없어요! `/알림설정`으로 추가해주세요.", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="📬 알림 설정 현황",
            color=0x5865F2
        )
        
        code_alerts = []
        yt_alerts = []
        update_alerts = []
        
        for type_key, channel_id in guild_settings[guild_id].items():
            if type_key.endswith("_community"):
                continue
            if type_key not in NOTIFY_TYPES:
                continue
            info = NOTIFY_TYPES[type_key]
            text = f"{info['emoji']} {info['name']}: <#{channel_id}>"
            if type_key.endswith("_yt"):
                yt_alerts.append(text)
            elif type_key == "hakushin_update":
                update_alerts.append(text)
            else:
                code_alerts.append(text)
        
        if code_alerts:
            embed.add_field(name="📋 코드 알림", value="\n".join(code_alerts), inline=False)
        if yt_alerts:
            embed.add_field(name="🎬 유튜브 알림 (커뮤니티 포함)", value="\n".join(yt_alerts), inline=False)
        if update_alerts:
            embed.add_field(name="🆕 신규 업데이트 알림", value="\n".join(update_alerts), inline=False)
        
        await interaction.response.send_message(embed=embed)
    
    @commands.command(name="알림설정")
    @commands.has_permissions(administrator=True)
    async def notify_setup(self, ctx):
        channel_id = ctx.channel.id
        
        embed = discord.Embed(
            title="📬 알림 설정",
            description=f"<#{channel_id}> 채널에 받을 알림을 선택하세요!\n\n**📋 코드 알림**: 리딤코드 자동 알림\n**🎬 유튜브 알림**: 새 영상 알림\n**🆕 신규 업데이트**: hakushin 신캐/무기/성유물 알림",
            color=0x5865F2
        )
        
        view = NotifySelectView(channel_id)
        await ctx.send(embed=embed, view=view)
    
    @commands.command(name="알림해제")
    @commands.has_permissions(administrator=True)
    async def notify_remove(self, ctx):
        guild_id = str(ctx.guild.id)
        current = guild_settings.get(guild_id, {})
        
        if not current:
            await ctx.send("❌ 설정된 알림이 없어요!")
            return
        
        embed = discord.Embed(
            title="🗑️ 알림 해제",
            description="해제할 알림을 선택하세요!",
            color=0xFF6B6B
        )
        
        view = RemoveNotifyView(guild_id, current)
        await ctx.send(embed=embed, view=view)
    
    @commands.command(name="알림현황")
    async def notify_status(self, ctx):
        guild_id = str(ctx.guild.id)
        
        if guild_id not in guild_settings or not guild_settings[guild_id]:
            await ctx.send("📭 설정된 알림이 없어요! `!알림설정`으로 추가해주세요.")
            return
        
        embed = discord.Embed(
            title="📬 알림 설정 현황",
            color=0x5865F2
        )
        
        code_alerts = []
        yt_alerts = []
        update_alerts = []
        
        for type_key, channel_id in guild_settings[guild_id].items():
            if type_key.endswith("_community"):
                continue
            if type_key not in NOTIFY_TYPES:
                continue
            info = NOTIFY_TYPES[type_key]
            text = f"{info['emoji']} {info['name']}: <#{channel_id}>"
            if type_key.endswith("_yt"):
                yt_alerts.append(text)
            elif type_key == "hakushin_update":
                update_alerts.append(text)
            else:
                code_alerts.append(text)
        
        if code_alerts:
            embed.add_field(name="📋 코드 알림", value="\n".join(code_alerts), inline=False)
        if yt_alerts:
            embed.add_field(name="🎬 유튜브 알림 (커뮤니티 포함)", value="\n".join(yt_alerts), inline=False)
        if update_alerts:
            embed.add_field(name="🆕 신규 업데이트 알림", value="\n".join(update_alerts), inline=False)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Settings(bot))
