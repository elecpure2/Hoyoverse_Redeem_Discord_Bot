import discord
from discord.ext import commands, tasks
import aiohttp
import re
from bs4 import BeautifulSoup
from utils.config import HOYO_GAME_CONFIGS, WUWA_CONFIG, ENDFIELD_CONFIG
from utils.data import load_sent_codes, save_sent_codes, get_channels_for_type
from cogs.settings import get_guild_settings

_loaded_codes = load_sent_codes()
already_sent_codes = {game: _loaded_codes.get(game, set()) for game in HOYO_GAME_CONFIGS}
already_sent_codes["wuwa"] = _loaded_codes.get("wuwa", set())
already_sent_codes["endfield"] = _loaded_codes.get("endfield", set())

async def fetch_hoyo_codes(api_url):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                if resp.status != 200:
                    print(f"코드 가져오기 실패: HTTP {resp.status}")
                    return []
                data = await resp.json()
                return data.get("codes", [])
    except aiohttp.ClientError as e:
        print(f"네트워크 오류: {e}")
        return []
    except Exception as e:
        print(f"코드 가져오기 중 예외 발생: {e}")
        return []

async def fetch_wuwa_codes():
    # 명조(WuWa)는 현재 실시간 코드를 제공하는 사이트가 없어 비활성화함.
    # (기존 wutheringwaves 위키가 403으로 차단되어 로그를 도배 → 네트워크 요청 자체를 제거)
    # 추후 안정적인 소스가 생기면 여기서 다시 구현하면 됨.
    return []

async def fetch_endfield_codes():
    try:
        async with aiohttp.ClientSession() as session:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
            async with session.get(ENDFIELD_CONFIG["url"], timeout=aiohttp.ClientTimeout(total=30), headers=headers) as resp:
                if resp.status != 200:
                    print(f"엔드필드 코드 가져오기 실패: HTTP {resp.status}")
                    return []
                html = await resp.text()
                soup = BeautifulSoup(html, 'lxml')
                
                codes = []
                # Game8 structure: Use all elements with class 'a-clipboard__textInput'
                # These inputs contain the code value.
                inputs = soup.find_all('input', class_='a-clipboard__textInput')
                
                for inp in inputs:
                    code = inp.get('value', '').strip()
                    if code and len(code) > 3:
                        # Try to find rewards in the same table row if possible
                        # Game8 tables usually have Code in one cell and Reward in another.
                        reward = "출시 기념 보상"
                        try:
                            # Search for reward text in the neighboring cells
                            parent_td = inp.find_parent('td')
                            if parent_td:
                                row = parent_td.find_parent('tr')
                                if row:
                                    cells = row.find_all('td')
                                    if len(cells) >= 2:
                                        # Usually Reward is in the second or third cell
                                        reward_text = cells[1].get_text(strip=True)
                                        if reward_text and reward_text != code:
                                            reward = reward_text
                        except:
                            pass
                            
                        codes.append({
                            "code": code,
                            "rewards": reward
                        })
                
                return codes
    except Exception as e:
        print(f"엔드필드 코드 가져오기 중 예외 발생: {e}")
        return []

def extract_currency_amount(reward, currency_keyword, currency_name):
    if not reward:
        return None
    
    reward_lower = reward.lower()
    if currency_keyword not in reward_lower:
        return None
    
    patterns = [
        rf'(\d+[\d,]*)\s*{re.escape(currency_keyword)}',
        rf'{re.escape(currency_keyword)}\s*[×x]\s*(\d+[\d,]*)',
        rf'(\d+[\d,]*)\s*x\s*{re.escape(currency_keyword)}',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, reward_lower)
        if match:
            amount = match.group(1).replace(',', '')
            return f"{currency_name} {amount}개"
    
    return None

class Redeem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_codes.start()
    
    def cog_unload(self):
        self.check_codes.cancel()
    
    @tasks.loop(minutes=5)
    async def check_codes(self):
        global already_sent_codes
        codes_updated = False
        guild_settings = get_guild_settings()
        
        for game_key, config in HOYO_GAME_CONFIGS.items():
            channels = get_channels_for_type(guild_settings, game_key)
            if not channels:
                continue

            codes = await fetch_hoyo_codes(config["api_url"])
            if not codes:
                continue

            new_list = []

            for item in codes:
                code = item.get("code")
                if not code:
                    continue

                if code not in already_sent_codes[game_key]:
                    already_sent_codes[game_key].add(code)
                    new_list.append(item)
                    codes_updated = True

            for item in new_list:
                code = item.get("code")
                reward = item.get("rewards", "")

                currency_info = extract_currency_amount(
                    reward, 
                    config["currency_keyword"], 
                    config["currency_name"]
                )

                redeem_url = f"{config['redeem_url']}{code}"
                
                if currency_info:
                    msg = f"🎁 [{code}](<{redeem_url}>) - {currency_info}"
                else:
                    msg = f"🎁 [{code}](<{redeem_url}>)"

                for channel_id in channels:
                    channel = self.bot.get_channel(channel_id)
                    if channel:
                        try:
                            await channel.send(msg)
                        except Exception as e:
                            print(f"채널 {channel_id}에 메시지 전송 실패: {e}")

            if new_list:
                print(f"[{config['name']}] 새 코드 전송:", [c.get("code") for c in new_list])

        wuwa_channels = get_channels_for_type(guild_settings, "wuwa")
        if wuwa_channels:
            codes = await fetch_wuwa_codes()
            
            new_list = []
            for item in codes:
                code = item.get("code")
                if not code:
                    continue

                if code not in already_sent_codes["wuwa"]:
                    already_sent_codes["wuwa"].add(code)
                    new_list.append(item)
                    codes_updated = True

            for item in new_list:
                code = item.get("code")
                reward = item.get("rewards", "")

                currency_info = extract_currency_amount(
                    reward, 
                    WUWA_CONFIG["currency_keyword"], 
                    WUWA_CONFIG["currency_name"]
                )

                msg = f"🎁 {code}"
                if currency_info:
                    msg += f" - {currency_info}"

                for channel_id in wuwa_channels:
                    channel = self.bot.get_channel(channel_id)
                    if channel:
                        try:
                            await channel.send(msg)
                        except Exception as e:
                            print(f"채널 {channel_id}에 메시지 전송 실패: {e}")

            if new_list:
                print(f"[{WUWA_CONFIG['name']}] 새 코드 전송:", [c.get("code") for c in new_list])
        
        # === Arknights: Endfield ===
        endfield_channels = get_channels_for_type(guild_settings, "endfield")
        if endfield_channels:
            codes = await fetch_endfield_codes()
            new_list = []
            for item in codes:
                code = item.get("code")
                if not code: continue
                if code not in already_sent_codes["endfield"]:
                    already_sent_codes["endfield"].add(code)
                    new_list.append(item)
                    codes_updated = True
            
            for item in new_list:
                code = item.get("code")
                reward = item.get("rewards", "")
                currency_info = extract_currency_amount(
                    reward, 
                    ENDFIELD_CONFIG["currency_keyword"], 
                    ENDFIELD_CONFIG["currency_name"]
                )
                msg = f"🎁 **{ENDFIELD_CONFIG['name']}**\n코드: `{code}`"
                if currency_info:
                    msg += f" - {currency_info}"
                
                for channel_id in endfield_channels:
                    channel = self.bot.get_channel(channel_id)
                    if channel:
                        try:
                            await channel.send(msg)
                        except Exception as e:
                            print(f"엔드필드 알림 전송 실패: {e}")
            if new_list:
                print(f"[{ENDFIELD_CONFIG['name']}] 새 코드 전송:", [c.get("code") for c in new_list])

        if codes_updated:
            save_sent_codes(already_sent_codes)
    
    @check_codes.before_loop
    async def before_check_codes(self):
        global already_sent_codes
        await self.bot.wait_until_ready()
        
        print("[리딤코드] 기존 코드 초기화 중...")
        
        for game_key, config in HOYO_GAME_CONFIGS.items():
            codes = await fetch_hoyo_codes(config["api_url"])
            for item in codes:
                code = item.get("code")
                if code:
                    already_sent_codes[game_key].add(code)
            print(f"  [{config['name']}] 기존 코드 {len(codes)}개 등록")
        
        wuwa_codes = await fetch_wuwa_codes()
        for item in wuwa_codes:
            code = item.get("code")
            if code:
                already_sent_codes["wuwa"].add(code)
        print(f"  [{WUWA_CONFIG['name']}] 기존 코드 {len(wuwa_codes)}개 등록")
        
        endfield_codes = await fetch_endfield_codes()
        for item in endfield_codes:
            code = item.get("code")
            if code:
                already_sent_codes["endfield"].add(code)
        print(f"  [{ENDFIELD_CONFIG['name']}] 기존 코드 {len(endfield_codes)}개 등록")
        
        save_sent_codes(already_sent_codes)
        print("[리딤코드] 초기화 완료! 이후 새 코드만 알림됩니다.")

async def setup(bot):
    await bot.add_cog(Redeem(bot))
