import discord
from discord import app_commands
from discord.ext import commands
import random
from utils.data import load_data, save_data

# 산드로네 일러스트. 출시 전엔 CDN(enka)에 없어 썸네일이 안 뜰 수 있으나(=미표시), 출시되면 자동 표시됨.
# 지금 바로 이미지를 띄우고 싶으면 HoYoLAB 등에서 받은 직링크로 교체하면 됨.
SANDRONE_IMAGE = "https://enka.network/ui/UI_Gacha_AvatarImg_MarionetteNew.png"

def do_single_pull(pity_5star, pity_4star):
    is_lucky = False
    if pity_5star >= 90:
        return 5, False
    elif pity_5star >= 77:
        soft_pity_rate = 0.006 + (pity_5star - 76) * 0.06
        if random.random() < soft_pity_rate:
            return 5, False
    else:
        if random.random() < 0.006:
            is_lucky = True
            return 5, is_lucky
    
    if pity_4star >= 10:
        return 4, False
    elif random.random() < 0.051:
        return 4, False
    
    return 3, False

class Gacha(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="기원리셋", description="기원 누적 기록을 초기화해요")
    async def slash_gacha_reset(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        data = load_data()
        
        if user_id in data["gacha_pity"]:
            data["gacha_pity"][user_id] = {
                "pity_5star": 0,
                "pity_4star": 0,
                "total_pulls": 0,
                "total_4star": 0,
                "total_columbina": 0,
                "total_qiqi": 0,
                "guaranteed": False
            }
            save_data(data)
        
        embed = discord.Embed(
            title="🔄 기원 기록 초기화",
            description="모든 천장과 누적 기록이 초기화되었습니다.",
            color=0x9966CC
        )
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="기원", description="산드로네 픽업 기원 시뮬레이터 (1~100회)")
    @app_commands.describe(횟수="기원 횟수 (1~100)")
    async def slash_gacha(self, interaction: discord.Interaction, 횟수: int = 1):
        if 횟수 < 1: 횟수 = 1
        if 횟수 > 100: 횟수 = 100
        
        user_id = str(interaction.user.id)
        embed = await self._do_gacha(user_id, 횟수, interaction.user.display_name)
        await interaction.response.send_message(embed=embed)
    
    @commands.command(name="기원리셋")
    async def gacha_reset(self, ctx):
        user_id = str(ctx.author.id)
        data = load_data()
        
        if user_id in data["gacha_pity"]:
            data["gacha_pity"][user_id] = {
                "pity_5star": 0,
                "pity_4star": 0,
                "total_pulls": 0,
                "total_4star": 0,
                "total_columbina": 0,
                "total_qiqi": 0,
                "guaranteed": False
            }
            save_data(data)
        
        embed = discord.Embed(
            title="🔄 기원 기록 초기화",
            description="모든 천장과 누적 기록이 초기화되었습니다.",
            color=0x9966CC
        )
        await ctx.send(embed=embed)
    
    @commands.command(name="기원")
    async def gacha(self, ctx, num: str = "1"):
        try:
            num_pulls = int(num)
        except ValueError:
            num_pulls = 1
            
        if num_pulls < 1: num_pulls = 1
        if num_pulls > 100: num_pulls = 100
        
        user_id = str(ctx.author.id)
        embed = await self._do_gacha(user_id, num_pulls, ctx.author.display_name)
        await ctx.send(embed=embed)
    
    async def _do_gacha(self, user_id, num_pulls, display_name):
        data = load_data()
        
        user_data = data["gacha_pity"].get(user_id, {})
        pity_5star = user_data.get("pity_5star", 0)
        pity_4star = user_data.get("pity_4star", 0)
        total_pulls = user_data.get("total_pulls", 0)
        total_4star = user_data.get("total_4star", 0)
        total_columbina = user_data.get("total_columbina", 0)
        total_qiqi = user_data.get("total_qiqi", 0)
        guaranteed = user_data.get("guaranteed", False)
        
        results = []
        five_star_logs = []
        
        got_5star = False
        got_columbina = False
        
        count_3star = 0
        count_4star = 0
        
        initial_pity = pity_5star
        
        for i in range(num_pulls):
            pity_5star += 1
            pity_4star += 1
            
            star, is_lucky = do_single_pull(pity_5star, pity_4star)
            
            total_pulls += 1
            
            if star == 5:
                got_5star = True
                
                # 로그 기록용 (몇 번째에 나왔나)
                pity_count = pity_5star
                
                pity_5star = 0
                pity_4star = 0
                
                if guaranteed:
                    # 확천장인 경우: 무조건 성공
                    results.append("🟡")
                    total_columbina += 1
                    got_columbina = True
                    guaranteed = False
                    five_star_logs.append(f"🟡 **산드로네** ({pity_count}회차) - *확정 천장*")
                elif random.random() < 0.5:
                    # 반천장 성공 (기본 50%)
                    results.append("🟡")
                    total_columbina += 1
                    got_columbina = True
                    guaranteed = False
                    five_star_logs.append(f"🟡 **산드로네** ({pity_count}회차) - *반천장 성공*")
                else:
                    # 반천장 실패 -> 별빛 포착(Capturing Radiance) 체크 (패배한 50% 중 10% 구제 = 전체 5%)
                    # 종합 확률 55% 달성
                    if random.random() < 0.1:
                        results.append("✨") # 별빛 포착 이모지 구분
                        total_columbina += 1
                        got_columbina = True
                        guaranteed = False
                        five_star_logs.append(f"✨ **산드로네** ({pity_count}회차) - **✨ 별빛 포착 발동!**")
                    else:
                        # 진짜 픽뚫
                        results.append("👻")
                        total_qiqi += 1
                        guaranteed = True
                        five_star_logs.append(f"👻 **치치** ({pity_count}회차)")

                # C6 달성 시 즉시 시뮬레이션 종료
                if total_columbina >= 7:
                    break
            elif star == 4:
                results.append("🟣")
                pity_4star = 0
                count_4star += 1
                total_4star += 1
            else:
                results.append("🔵")
                count_3star += 1
        
        # 데이터 저장
        if user_id not in data["gacha_pity"]:
            data["gacha_pity"][user_id] = {}
        data["gacha_pity"][user_id].update({
            "pity_5star": pity_5star,
            "pity_4star": pity_4star,
            "total_pulls": total_pulls,
            "total_4star": total_4star,
            "total_columbina": total_columbina,
            "total_qiqi": total_qiqi,
            "guaranteed": guaranteed
        })
        save_data(data)
        
        # 결과 그리드: 모든 뽑기를 5개씩 동그라미로 나열 (5성이 어디서 떴는지 한눈에)
        display_str = ""
        for i, res in enumerate(results):
            display_str += res + " "
            if (i + 1) % 5 == 0:
                display_str += "\n"
        legend = "🟡 산드로네 · 👻 치치 · ✨ 별빛 포착 · 🟣 4성 · 🔵 3성"

        # 임베드 생성 (1·10·100뽑 모두 동그라미 그리드로 시각화)
        if num_pulls > 10:
            title = "✨ 산드로네 획득! ✨" if got_columbina else "💫 산드로네 픽업 기원 결과"
            embed = discord.Embed(
                title=f"{title} ({num_pulls}회)",
                description=f"{display_str}\n{legend}",
                color=0xFFD700 if got_columbina else 0x9966CC,
            )

            if five_star_logs:
                embed.add_field(name="⭐ 5성 획득", value="\n".join(five_star_logs), inline=False)
            else:
                embed.add_field(name="⭐ 5성 획득", value="없음... (다음엔 꼭!)", inline=False)

            embed.add_field(name="결과 요약", value=f"🟣 4성 {count_4star}개   ·   🔵 3성 {count_3star}개", inline=False)

            status_msg = f"다음 5성까지 **{90 - pity_5star}회** 남음"
            status_msg += " (확정 천장 🔥)" if guaranteed else " (반천장 🎲)"
            embed.add_field(name="📊 현재 상태", value=status_msg, inline=False)

        else:
            title = "💫 기원 결과"
            if got_columbina:
                title = "✨ 산드로네 획득! ✨"
                color = 0xFFD700
            elif got_5star:
                title = "👻 치치가 왔습니다..."
                color = 0x808080
            else:
                color = 0x9966CC

            embed = discord.Embed(title=title, description=display_str, color=color)
            
            obtained = []
            if got_columbina: obtained.append("산드로네")
            if any(r == "👻" for r in results): obtained.append("치치")
            if count_4star > 0: obtained.append("4성 아이템")
            if not obtained: obtained.append("3성 무기")
            
            embed.add_field(name="획득 목록", value=", ".join(obtained), inline=False)
            embed.add_field(name="현재 천장", value=f"{pity_5star}/90", inline=True)
            
        # C6 달성 체크 (7장 획득 시)
        if total_columbina >= 7:
            # 통계 계산
            average_pulls = 655
            efficiency = (average_pulls - total_pulls) / average_pulls * 100
            total_primogems = total_pulls * 160
            
            luck_msg = ""
            if efficiency >= 50:
                luck_msg = "🌟 **초비틱!** (상위 1% 운빨)"
            elif efficiency >= 20:
                luck_msg = "🍀 **운이 아주 좋네요!**"
            elif efficiency >= 0:
                luck_msg = "🙂 **평균보다 조금 덜 썼어요.**"
            elif efficiency >= -20:
                luck_msg = "😅 **평균보다 조금 더 썼네요...**"
            else:
                luck_msg = "💀 **폭사... (다음엔 잘 될 거예요)**"

            # C6 완료 임베드 생성
            embed = discord.Embed(title="👑 **산드로네 6돌파(C6) 달성!** 👑", description="축하합니다! 졸업하셨습니다! 🎉", color=0xFF0000)
            
            embed.add_field(name="📉 **총 소모 기원**", value=f"{total_pulls}회\n({total_primogems:,} 원석)", inline=True)
            embed.add_field(name="👻 **총 픽뚫(치치)**", value=f"{total_qiqi}회", inline=True)
            embed.add_field(name="📊 **운세 분석**", value=f"{luck_msg}\n(평균 655회 대비 {efficiency:.1f}% 효율)", inline=False)
            
            if SANDRONE_IMAGE:
                embed.set_thumbnail(url=SANDRONE_IMAGE)
            embed.set_footer(text="데이터가 초기화되었습니다. 다시 1회부터 시작할 수 있습니다.")

            # 데이터 초기화
            del data["gacha_pity"][user_id]
            save_data(data)
            
            return embed

        # 별자리(돌파) 계산
        constellation = total_columbina - 1
        if constellation < 0:
            c_status = "미보유"
        elif constellation == 0:
            c_status = "명함 (C0)"
        else:
            c_status = f"{constellation}돌파 (C{constellation})"
            
        footer_text = f"누적: {total_pulls}회 | 산드로네: {c_status} | 픽뚫(치치): {total_qiqi}회"
        if SANDRONE_IMAGE:
            embed.set_thumbnail(url=SANDRONE_IMAGE)
        embed.set_footer(text=footer_text)
        return embed

async def setup(bot):
    await bot.add_cog(Gacha(bot))
