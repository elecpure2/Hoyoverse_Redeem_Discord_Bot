import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
from utils.config import AVATAR_ICON_NAMES, COSTUME_ART_NAMES, CHARACTER_NAME_TO_ENKA, AVATAR_ID_TO_KR
from utils.data import load_uid_data, save_uid_data
from utils.enka_locale import get_character_name_kr

class CharacterSelect(discord.ui.Select):
    def __init__(self, characters, uid, bot):
        self.uid = uid
        self.bot = bot
        options = []
        for char_id, char_name in characters[:25]:
            options.append(discord.SelectOption(label=char_name, value=str(char_id)))
        super().__init__(placeholder="캐릭터를 선택하세요...", options=options)
    
    async def callback(self, interaction: discord.Interaction):
        char_id = int(self.values[0])
        char_name = await get_character_name_kr(char_id)
        await interaction.response.send_message(f"🔍 **{char_name}** 빌드를 불러오는 중...", ephemeral=True)
        await show_build_for_uid(interaction.channel, interaction.user, self.uid, char_name, char_id)

class CharacterSelectView(discord.ui.View):
    def __init__(self, characters, uid, bot):
        super().__init__(timeout=60)
        self.add_item(CharacterSelect(characters, uid, bot))

async def show_build_for_uid(channel, user, uid, char_name, target_avatar_id=None):
    try:
        async with aiohttp.ClientSession() as session:
            headers = {"User-Agent": "HoyoRedeemBot/1.0"}
            async with session.get(f"https://enka.network/api/uid/{uid}/", headers=headers) as resp:
                if resp.status != 200:
                    await channel.send(f"❌ API 오류: {resp.status}")
                    return
                data = await resp.json()
    except Exception as e:
        await channel.send(f"❌ 연결 오류: {e}")
        return
    
    avatar_list = data.get("avatarInfoList", [])
    if not avatar_list:
        await channel.send("📭 전시된 캐릭터가 없어요!")
        return
    
    found_avatar = None
    for avatar in avatar_list:
        avatar_id = avatar.get("avatarId", 0)
        if target_avatar_id and avatar_id == target_avatar_id:
            found_avatar = avatar
            break
        kr_name = await get_character_name_kr(avatar_id)
        if kr_name == char_name or char_name in kr_name:
            found_avatar = avatar
            break
    
    if not found_avatar:
        await channel.send(f"❌ `{char_name}` 캐릭터를 찾을 수 없어요!")
        return
    
    avatar_id = found_avatar.get("avatarId", 0)
    char_kr = await get_character_name_kr(avatar_id) if avatar_id else char_name
    
    player_info = data.get("playerInfo", {})
    nickname = player_info.get("nickname", "알 수 없음")
    
    props = found_avatar.get("propMap", {})
    fight_props = found_avatar.get("fightPropMap", {})
    
    level = props.get("4001", {}).get("val", "?")
    ascension = props.get("1002", {}).get("val", 0)
    constellation = len(found_avatar.get("talentIdList", []))
    
    hp = int(fight_props.get("2000", 0))
    atk = int(fight_props.get("2001", 0))
    defense = int(fight_props.get("2002", 0))
    em = int(fight_props.get("28", 0))
    crit_rate = fight_props.get("20", 0) * 100
    crit_dmg = fight_props.get("22", 0) * 100
    er = fight_props.get("23", 0) * 100
    
    equip_list = found_avatar.get("equipList", [])
    weapon_info = None
    artifact_sets = {}
    
    for equip in equip_list:
        if "weapon" in equip:
            weapon = equip.get("weapon", {})
            # 무기 재련 계산 개선
            affix_map = weapon.get("affixMap", {})
            refine = 1  # 기본값
            if affix_map:
                # affixMap의 첫 번째 키의 값을 가져와서 +1
                first_key = list(affix_map.keys())[0] if affix_map else None
                if first_key:
                    refine = affix_map.get(first_key, 0) + 1
            
            weapon_info = {
                "level": weapon.get("level", 1),
                "refine": refine,
            }
        elif "reliquary" in equip:
            set_name = equip.get("flat", {}).get("setNameTextMapHash", "")
            artifact_sets[set_name] = artifact_sets.get(set_name, 0) + 1
    
    set_bonuses = []
    for set_hash, count in artifact_sets.items():
        if count >= 4:
            set_bonuses.append("4세트")
        elif count >= 2:
            set_bonuses.append("2세트")
    
    color = 0x5865F2
    
    embed = discord.Embed(
        title=f"🏆 {char_kr} 빌드",
        description=f"**{nickname}** | UID: {uid}",
        color=color
    )
    
    icon_name = AVATAR_ICON_NAMES.get(avatar_id, "PlayerBoy")
    costume_id = found_avatar.get("costumeId")
    
    if costume_id and costume_id in COSTUME_ART_NAMES:
        costume_name = COSTUME_ART_NAMES[costume_id]
        side_icon_url = f"https://enka.network/ui/UI_AvatarIcon_Side_{costume_name}.png"
    else:
        side_icon_url = f"https://enka.network/ui/UI_AvatarIcon_Side_{icon_name}.png"
    
    # Enka Card 이미지 URL 생성 (반드시 /image를 붙여야 이미지로 반환됨)
    card_url = f"https://cards.enka.network/u/{uid}/{avatar_id}/image"
    embed.set_image(url=card_url)
    
    # 등급 아이콘 설정 (기존 섬네일 대체 또는 생략)
    # embed.set_thumbnail(url=side_icon_url) # 카드 이미지가 메인이므로 섬네일은 제거하거나 작게 유지
    
    const_icons = []
    for i in range(6):
        if i < constellation:
            const_icons.append("⭐")
        else:
            const_icons.append("🔒")
    const_display = "".join(const_icons)
    
    # 특성 레벨 가져오기 (skillLevelMap + proudSkillExtraLevelMap)
    skill_level_map = found_avatar.get("skillLevelMap", {})
    proud_skill_map = found_avatar.get("proudSkillExtraLevelMap", {})
    
    # 스킬 ID 정렬 (보통 평타(1) -> 스킬(2) -> 궁(5) 순서로 ID가 배정됨)
    sorted_skills = sorted(skill_level_map.keys())
    
    talent_texts = []
    for skill_id_str in sorted_skills:
        skill_id = int(skill_id_str)
        base_lvl = skill_level_map[skill_id_str]
        bonus = 0
        
        # 휴리스틱: 스킬 ID의 마지막 자리가 2면 전투스킬, 5면 궁극기일 확률이 높음
        # ProudGroup ID의 마지막 자리가 2면 전투스킬 보너스, 9면 궁극기 보너스일 확률이 높음
        last_digit = skill_id % 10
        
        # 보너스 매칭 시도
        for proud_key, proud_val in proud_skill_map.items():
            proud_id = int(proud_key)
            proud_last = proud_id % 10
            
            if last_digit == 2 and proud_last == 2: # 전투스킬 매칭
                bonus = proud_val
                break
            elif last_digit == 5 and proud_last == 9: # 궁극기 매칭
                bonus = proud_val
                break
            # 일부 구형 캐릭터나 예외 케이스 처리 (ID + 10 패턴 등)은 생략하고 가장 일반적인 패턴만 적용
            
        final_lvl = base_lvl + bonus
        
        # 보너스가 있으면 색상 강조 (파란색) - 디스코드에선 bold 등으로 표현
        if bonus > 0:
            talent_texts.append(f"**{final_lvl}**")
        else:
            talent_texts.append(str(final_lvl))

    talent_display = " / ".join(talent_texts)
    if not talent_display:
        talent_display = "정보 없음"
    
    # 치명타 밸류 (CV) 계산 및 등급 산정 (사용자 요청 기준)
    match_cv_score = crit_rate * 2 + crit_dmg
    if match_cv_score >= 350:
        grade = "SS (종결)"
        grade_emoji = "👑"
    elif match_cv_score >= 280:
        grade = "S (준종결)"
        grade_emoji = "💠"
    elif match_cv_score >= 200:
        grade = "A (쓸만함)"
        grade_emoji = "✅"
    else:
        grade = "B (성장 필요)"
        grade_emoji = "🌱"
    
    # 상세 스탯 텍스트 복구 (이미지가 안 보일 때를 대비해 필수 정보 포함)
    stats_text = f"""
> **{grade_emoji} 종합 등급: {grade}**
> (CV: {match_cv_score:.1f})

**[기본 스펙]**
❤️ HP: `{hp:,}`
⚔️ 공격력: `{atk:,}`
🛡️ 방어력: `{defense:,}`
✨ 원마: `{em}`

**[전투 스탯]**
🎯 치확: `{crit_rate:.1f}%`
💥 치피: `{crit_dmg:.1f}%`
⚡ 원충: `{er:.1f}%`

**[장비 정보]**
🗡️ 무기: Lv.{weapon_info['level'] if weapon_info else '?'} (재련 {weapon_info['refine'] if weapon_info else '?'})
🌟 별자리: {constellation}돌파 (C{constellation})
⚡ 특성: **{talent_display}**
"""
    embed.add_field(name="📊 상세 분석", value=stats_text.strip(), inline=False)
    
    embed.set_footer(text="Enka.network 제공 | 이미지가 로딩되지 않으면 위 텍스트를 참고하세요.")
    
    await channel.send(embed=embed)

class Enka(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="uid", description="UID를 등록하고 전시 캐릭터를 확인해요")
    @app_commands.describe(uid="원신 UID (9자리)")
    async def slash_uid(self, interaction: discord.Interaction, uid: str):
        if not uid.isdigit() or len(uid) != 9:
            await interaction.response.send_message("❌ UID는 9자리 숫자여야 해요!", ephemeral=True)
            return
        
        user_id = str(interaction.user.id)
        uid_data = load_uid_data()
        uid_data[user_id] = uid
        save_uid_data(uid_data)
        
        await interaction.response.defer()
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {"User-Agent": "HoyoRedeemBot/1.0"}
                async with session.get(f"https://enka.network/api/uid/{uid}/", headers=headers) as resp:
                    if resp.status == 424:
                        await interaction.followup.send(f"✅ UID `{uid}` 등록 완료!\n⚠️ 게임 점검 중이라 캐릭터 조회 불가")
                        return
                    if resp.status == 429:
                        await interaction.followup.send(f"✅ UID `{uid}` 등록 완료!\n⚠️ 잠시 후 `/전시`로 확인해주세요")
                        return
                    if resp.status != 200:
                        await interaction.followup.send(f"✅ UID `{uid}` 등록 완료!\n❌ API 오류: {resp.status}")
                        return
                    data = await resp.json()
        except Exception as e:
            await interaction.followup.send(f"✅ UID `{uid}` 등록 완료!\n❌ 연결 오류: {e}")
            return
        
        player_info = data.get("playerInfo", {})
        nickname = player_info.get("nickname", "알 수 없음")
        level = player_info.get("level", "?")
        
        avatar_list = data.get("avatarInfoList", [])
        
        if not avatar_list:
            await interaction.followup.send(f"✅ UID `{uid}` 등록 완료!\n\n📭 **{nickname}** (AR {level})\n전시된 캐릭터가 없어요! 게임에서 캐릭터 전시 설정을 확인해주세요.")
            return
        
        characters = []
        for avatar in avatar_list:
            avatar_id = avatar.get("avatarId", 0)
            kr_name = await get_character_name_kr(avatar_id)
            characters.append((avatar_id, kr_name))
        
        embed = discord.Embed(
            title=f"✅ UID 등록 완료!",
            description=f"**{nickname}** (AR {level}) | UID: {uid}",
            color=0x00FF00
        )
        
        if characters:
            char_list = "\n".join([f"• {name}" for _, name in characters])
            embed.add_field(name=f"🎭 전시 캐릭터 ({len(characters)}명)", value=char_list, inline=False)
        else:
            embed.add_field(name="🎭 전시 캐릭터", value="전시된 캐릭터가 없어요!", inline=False)
        embed.set_footer(text="아래 드롭다운에서 캐릭터를 선택하세요!")
        
        view = CharacterSelectView(characters, uid, self.bot)
        await interaction.followup.send(embed=embed, view=view)
    
    @commands.command(name="uid", aliases=["UID", "Uid", "uid입력"])
    async def uid_register(self, ctx, uid: str = None):
        if not uid or not uid.isdigit() or len(uid) != 9:
            await ctx.send("❌ 사용법: `!uid 123456789` (9자리)")
            return
        
        user_id = str(ctx.author.id)
        uid_data = load_uid_data()
        uid_data[user_id] = uid
        save_uid_data(uid_data)
        
        async with ctx.typing():
            try:
                async with aiohttp.ClientSession() as session:
                    headers = {"User-Agent": "HoyoRedeemBot/1.0"}
                    async with session.get(f"https://enka.network/api/uid/{uid}/", headers=headers) as resp:
                        if resp.status == 424:
                            await ctx.send(f"✅ UID `{uid}` 등록 완료!\n⚠️ 게임 점검 중이라 캐릭터 조회 불가")
                            return
                        if resp.status == 429:
                            await ctx.send(f"✅ UID `{uid}` 등록 완료!\n⚠️ 잠시 후 `!전시`로 확인해주세요")
                            return
                        if resp.status != 200:
                            await ctx.send(f"✅ UID `{uid}` 등록 완료!\n❌ API 오류: {resp.status}")
                            return
                        data = await resp.json()
            except Exception as e:
                await ctx.send(f"✅ UID `{uid}` 등록 완료!\n❌ 연결 오류: {e}")
                return
        
        player_info = data.get("playerInfo", {})
        nickname = player_info.get("nickname", "알 수 없음")
        level = player_info.get("level", "?")
        
        avatar_list = data.get("avatarInfoList", [])
        
        if not avatar_list:
            await ctx.send(f"✅ UID `{uid}` 등록 완료!\n\n📭 **{nickname}** (AR {level})\n전시된 캐릭터가 없어요! 게임에서 캐릭터 전시 설정을 확인해주세요.")
            return
        
        characters = []
        for avatar in avatar_list:
            avatar_id = avatar.get("avatarId", 0)
            kr_name = await get_character_name_kr(avatar_id)
            characters.append((avatar_id, kr_name))
        
        embed = discord.Embed(
            title=f"✅ UID 등록 완료!",
            description=f"**{nickname}** (AR {level}) | UID: {uid}",
            color=0x00FF00
        )
        
        if characters:
            char_list = "\n".join([f"• {name}" for _, name in characters])
            embed.add_field(name=f"🎭 전시 캐릭터 ({len(characters)}명)", value=char_list, inline=False)
        else:
            embed.add_field(name="🎭 전시 캐릭터", value="전시된 캐릭터가 없어요!", inline=False)
        embed.set_footer(text="아래 드롭다운에서 캐릭터를 선택하세요!")
        
        view = CharacterSelectView(characters, uid, self.bot)
        await ctx.send(embed=embed, view=view)
    
    @commands.command(name="빌드")
    async def build(self, ctx, *, 캐릭터: str = None):
        if not 캐릭터:
            await ctx.send("❌ 사용법: `!빌드 피슬` 또는 `!빌드 Fischl`")
            return
        
        user_id = str(ctx.author.id)
        uid_data = load_uid_data()
        
        if user_id not in uid_data:
            await ctx.send("❌ 먼저 UID를 등록해주세요! `!uid 123456789`")
            return
        
        uid = uid_data[user_id]
        
        async with ctx.typing():
            await show_build_for_uid(ctx.channel, ctx.author, uid, 캐릭터)
    
async def setup(bot):
    await bot.add_cog(Enka(bot))
