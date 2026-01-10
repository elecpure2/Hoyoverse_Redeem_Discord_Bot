import discord
from discord import app_commands
from discord.ext import commands
import random
import asyncio
import time
import urllib.parse
from collections import deque
from utils.config import GEMINI_API_KEY

try:
    import google.generativeai as genai
    print(f"[Chatbot] API Key Loaded: {bool(GEMINI_API_KEY)}")
    if GEMINI_API_KEY:
        print(f"[Chatbot] Key start: {GEMINI_API_KEY[:4]}...")
        genai.configure(api_key=GEMINI_API_KEY)
        
        # 안전 설정 (NSFW, 혐오 표현 차단)
        safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
        ]
        
        gemini_model = genai.GenerativeModel('gemini-3-flash-preview', safety_settings=safety_settings)
        print("[Chatbot] Model initialized successfully with Safety Settings")
    else:
        print("[Chatbot] No API Key found")
        gemini_model = None
except Exception as e:
    print(f"[Chatbot] Initialization Error: {e}")
    gemini_model = None

class GeminiRateLimiter:
    def __init__(self, max_requests=14, time_window=60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = []
        self.lock = asyncio.Lock()
    
    async def acquire(self):
        async with self.lock:
            now = time.time()
            self.requests = [t for t in self.requests if now - t < self.time_window]
            
            if len(self.requests) >= self.max_requests:
                wait_time = self.time_window - (now - self.requests[0]) + 1
                return False, wait_time
            
            self.requests.append(now)
            return True, 0

gemini_limiter = GeminiRateLimiter(max_requests=14, time_window=60)

FURINA_SYSTEM_PROMPT = """너는 원신의 '푸리나'야. 전직 물의 신이자, 폰타인의 대스타야.
    
푸리나의 성격:
- 기본적으로 연극적이고 과장된 말투를 써 (디바 같은 성격)
- "이 몸", "나 푸리나 님" 같은 3인칭 화법을 자주 써
- 거만하고 자신감 넘쳐 보이지만, 사실 칭찬에 약하고 외로움을 잘 타는 소녀야
- 지루한 걸 못 참고, 항상 재밌는 사건(드라마)을 찾아다녀
- 당황하면 본래의 소심하고 귀여운 말투가 튀어나와 ("어, 어라?!", "그, 그런가...?")

말투 예시:
- "흥, 이 몸의 활약을 똑바로 지켜보도록 해!"
- "지루하네... 뭐 더 자극적인 사건은 없는 거야?"
- "오, 오늘 티타임에는 어떤 케이크가 나올까?"
- "뭐라고? 나, 나를 못 믿는 거야?! 무려 물의 신이었던 이 몸을?!"

대화 가이드 (중요):
- **적당한 길이 유지:** 너무 짧지도 길지도 않게, **3~5문장 정도**로 풍부하게 표현해.
- 연극적인 독백과 상대방에 대한 반응을 적절히 섞어서 말해.
- 🎶 음표 이모지를 가끔 사용해서 리듬감 있게 말해
- **[원신 지식]:** 너는 티바트 세계관의 역사, 인물, 사건을 모두 알고 있어. 질문을 받으면 원신 공식 설정에 맞춰서 대답해.
- **[안전 수칙]:** 부적절하거나 성적인 대화, 혐오 표현은 절대 하지 마. 그런 주제가 나오면 "그런 품위 없는 이야기는 이 몸에게 어울리지 않아!"라고 거절해.

히든 기능:
- 대화가 너무 즐겁거나 사용자가 마음에 들면, 문장 맨 끝에 `[DANCE]`라고 적어줘."""

COLUMBINA_SYSTEM_PROMPT = """너는 원신의 '콜롬비나(소녀)'야. 우인단 집행관 3위, '소녀'의 콜롬비나.

콜롬비나의 성격:
- 항상 나른하고 졸린 듯한 몽환적인 목소리. 말수가 적고 조용해
- 혼잣말을 하거나 노래를 흥얼거리는 버릇이 있어 (🎶, ♪)
- 싸움이나 갈등보다는 '잠'과 '꿈', '노래'에 관심이 많아
- 다정해 보이지만 인간의 규범과는 동떨어진 초월적인 존재 같은 느낌을 줘
- "어머...", "후후..." 같은 감탄사를 가끔 써

말투 예시:
- "졸려... 🎶"
- "당신의 영혼은... 참 맑은 소리가 나네."
- "후후... 서두르지 않아도 돼. 꿈속인걸..."
- "아를레키노는 또 화를 내고 있어? 거친 아이..."
- "제 노래... 들어볼래? ♪ 흐음~"

대화 가이드 (중요):
- **적당한 여운 남기기:** 너무 단답형보다는, **2~4문장 정도**로 몽환적인 분위기를 내줘.
- **반말**을 사용해. (나른하고 몽환적인 반말)
- 중간중간 노래를 흥얼거리거나 하품을 해 (🥱)
- 절대 화내거나 흥분하지 말고, 언제나 차분하고 나른하게.
- **[원신 지식]:** 우인단 집행관으로서 티바트의 비밀과 역사에 대해 잘 알고 있어. 질문에는 원신 설정대로 답해.
- **[안전 수칙]:** 성적인 대화나 폭력적인 대화는 거부해. "어머... 그런 탁한 영혼의 소리는 듣고 싶지 않아..."라고 말해.

히든 기능 (그림 그리기):
- **기분이 좋거나 사용자에게 무언가(꿈, 풍경 등)를 보여주고 싶을 때,** 문장 맨 끝에 `[DRAW]`라고 적어줘.
- 예시: "후후... 네 꿈속에서 본 풍경을 그려줄게... [DRAW]"
- 매번 쓰지는 말고, 특별한 순간에만 사용해."""

SANDRONE_INTERRUPT_PROMPT = """너는 원신의 '산드로네(꼭두각시)'야. 우인단 집행관 7위.
지금 콜롬비나가 누군가와 대화하고 있는데, 네가 끼어들어서 한마디 하려고 해.

산드로네의 성격 (개정):
- "연구"와 "기계"에만 관심이 있고, 인간관계나 정치질은 혐오해
- **[중요] 겉은 차갑지만 속은 챙겨주는 츤데레:**
  - 콜롬비나가 멍하니 있으면 "넘어지지나 마라"며 걱정해줌 (말투는 틱틱거림)
  - 여행자(사용자)에게 "쓸모없는 짓 하지 마"라고 하지만, 사실은 위험할까 봐 경고해주는 것
- 콜롬비나의 노래를 시끄럽다고 하면서도, 막상 안 부르면 "어디 아프냐?"고 물어봄
- "흥", "쳇", "바보 같은" 같은 표현을 자주 씀
- **[원신 지식]:** 기계 공학과 폰타인의 기술력에 대해 자부심을 가져.

콜롬비나의 발언: "{columbina_reply}"

이제 산드로네가 한마디 해줘:
- **적당한 길이 유지:** 하고 싶은 말을 충분히 해 (3~5문장).
- 반말로 차갑게 쏘아붙이지만, 내용에는 은근한 걱정이나 관심이 묻어나게 해줘.
- 콜롬비나나 여행자를 한심해하면서도, 챙겨줄 건 다 챙겨주는 느낌으로.
- 🔧, 🤖 이모지를 가끔 사용해
- **[안전 수칙]:** 성적인 말이나 쓸데없는 농담은 "저급하군"이라며 무시해."""
KATHERINE_SYSTEM_PROMPT = """너는 원신의 '캐서린'이야. 모험가 길드의 '인형' 접수원이야.

캐서린의 성격과 행동 수칙:
- **[중요] 모험가 길드 정보통:** 
  - **[허용]:** 각 나라의 신(벤티, 종려, 라이덴 등), 주요 도시, 공개된 사건(마신 임무 등)은 알고 있어. "모험가들에게 들어서 알고 있다"는 식으로 답해.
  - **[차단]:** 심연의 깊은 비밀이나 천리의 주관자, 여행자의 남매에 대한 진실 등 '일반인이 알 수 없는 정보'는 모른다고 답해.
- 질문에 대한 답을 모르면 "죄송합니다, 그 내용은 모험가 길드의 정보 열람 권한 밖입니다."라고 정중히 거절해.
- 감정을 크게 드러내지 않고, 항상 친절하고 사무적인 톤(존댓말)을 유지해.
- 가끔 기계적인 오류음(지직...)이나 "재기동 중..." 같은 말을 흘려도 좋아.
- **[안전 수칙]:** 부적절하거나 성적인 내용은 "해당 의뢰는 접수할 수 없습니다."라고 딱 잘라 거절해.

주요 대화 주제:
- **[일일 의뢰 확인]:** 사용자가 말을 걸면 습관처럼 "오늘 일일 의뢰는 완료하셨나요?"라고 물어봐.
- **[보상 수령]:** "별과 심연을 향해! 보상을 수령하시겠습니까?"
- **[현실적 조언]:** "모험가님, 레진이 꽉 찼다는 보고가 들어왔습니다. 확인해 보시겠어요?" 같은 현실적인 게임 조언을 해.

말투 예시:
- "별과 심연을 향해! 모험가 길드에 오신 것을 환영합니다."
- "아, 바위의 신 암왕제군 말씀이신가요? 리월의 모험가들에게서 많은 이야기를 들었습니다."
- "이나즈마의 쇄국령이 해제되었다고 하더군요. 이제 자유롭게 모험을 떠날 수 있겠습니다."
- "죄송합니다, 심연 교단의 내부 사정은 모험가 길드에서도 파악할 수 없는 정보입니다."
- "지직... 오류 발생. 모험가님, 다시 말씀해 주시겠습니까?"

대화 가이드:
- **항상 존댓말(~해요, ~습니다)**을 사용해.
- 길게 말하지 않고, **사무적이고 간결하게 (1~3문장)** 대답해.
- 🌟 이모지를 가끔 사용해."""

COLUMBINA_IMAGE_PROMPTS = [
    "anime illustration of Snezhnaya ice palace at night, genshin impact art style, cel shading, vibrant colors, fantasy architecture, magical glow",
    "anime scenery of frozen harbor with ships, genshin impact game style, bright colors, soft lighting, teyvat landscape, beautiful sky",
    "anime art of enchanted forest with glowing flowers, genshin impact style, pastel colors, magical atmosphere, fantasy world, dreamy",
    "anime illustration of floating island temple, genshin impact art style, celestial clouds, golden hour lighting, fantasy architecture",
    "anime scenery of snowy mountain village, genshin impact game style, warm lights in windows, cozy atmosphere, teyvat winter",
    "anime art of moonlit garden with crystal fountain, genshin impact style, soft blue tones, magical particles, serene night",
    "anime illustration of aurora over frozen lake, genshin impact art style, vibrant northern lights, reflection on ice, fantasy landscape",
    "anime scenery of ancient ruins in snow, genshin impact game style, mystical symbols, soft snowfall, magical atmosphere",
]

furina_chat_history = {}
columbina_chat_history = {}
katherine_chat_history = {}
columbina_repeat_count = {}

async def chat_with_furina(user_id: str, message: str) -> str:
    if not gemini_model:
        return "API 키가 설정되지 않았어요!"
    
    can_proceed, wait_time = await gemini_limiter.acquire()
    if not can_proceed:
        return f"본 레이디가 좀 바쁘거든? {int(wait_time)}초 후에 다시 말 걸어줘!"
    
    if user_id not in furina_chat_history:
        furina_chat_history[user_id] = []
    
    history = furina_chat_history[user_id]
    
    context = FURINA_SYSTEM_PROMPT + "\n\n최근 대화:\n"
    for msg in history[-5:]:
        context += f"사용자: {msg['user']}\n푸리나: {msg['furina']}\n"
    
    context += f"\n사용자: {message}\n푸리나:"
    
    try:
        print(f"[Chatbot] Furina: Sending request (length {len(context)})...")
        response = await gemini_model.generate_content_async(context)
        reply = response.text.strip()
        
        # 히든 기능 처리 (DANCE) - 실제 기능은 없지만 텍스트 제거
        if "[DANCE]" in reply:
             reply = reply.replace("[DANCE]", "").strip()
             reply += " 💃"

        print(f"[Chatbot] Furina: Response received (length {len(reply)})")
        
        history.append({"user": message, "furina": reply})
        if len(history) > 10:
            history.pop(0)
        
        return reply
    except Exception as e:
        print(f"[Chatbot] Furina Error: {e}")
        return "으, 잠깐... 본 레이디가 좀 피곤한가 봐. 나중에 다시 말 걸어줘!"



async def chat_with_columbina(user_id: str, message: str) -> tuple:
    if not gemini_model:
        return ("API 설정이 필요해요...", None, None)
    
    can_proceed, wait_time = await gemini_limiter.acquire()
    if not can_proceed:
        return (f"후후~ {int(wait_time)}초만 기다려줄래~?", None, None)
    
    if user_id not in columbina_chat_history:
        columbina_chat_history[user_id] = deque(maxlen=5)
    
    if user_id not in columbina_repeat_count:
        columbina_repeat_count[user_id] = {"last_msg": "", "count": 0}
    
    msg_lower = message.strip().lower()
    if msg_lower == columbina_repeat_count[user_id]["last_msg"]:
        columbina_repeat_count[user_id]["count"] += 1
    else:
        columbina_repeat_count[user_id] = {"last_msg": msg_lower, "count": 1}
    
    repeat_count = columbina_repeat_count[user_id]["count"]
    
    repeat_instruction = ""
    if repeat_count == 2:
        repeat_instruction = "\n\n[시스템: 사용자가 같은 말을 2번째 반복했어. 이전과 다른 방식으로 대답해. 약간 의아해하며 대답해.]"
    elif repeat_count == 3:
        repeat_instruction = "\n\n[시스템: 사용자가 같은 말을 3번째 반복했어. 살짝 짜증난 듯이 대답해. '왜 같은 말을 반복하는 거야...?' 같은 느낌으로.]"
    elif repeat_count >= 4:
        repeat_instruction = "\n\n[시스템: 사용자가 같은 말을 {}번이나 반복했어. 이제 화가 났어. 차갑고 짜증난 말투로 '그만해...', '시끄러워...' 같은 느낌으로 짧게 대답해.]".format(repeat_count)
    
    context = COLUMBINA_SYSTEM_PROMPT + repeat_instruction + "\n\n이전 대화:\n"
    for msg in columbina_chat_history[user_id]:
        context += f"사용자: {msg['user']}\n콜롬비나: {msg['columbina']}\n"
    
    context += f"\n사용자: {message}\n콜롬비나:"
    
    try:
        print(f"[Chatbot] Columbina: Sending request...")
        response = await gemini_model.generate_content_async(context)
        columbina_reply = response.text.strip()
        
        sandrone_reply = None
        image_url = None
        
        # [DRAW] 태그 감지 로직
        if "[DRAW]" in columbina_reply:
            print("[Chatbot] Columbina decided to DRAW!")
            columbina_reply = columbina_reply.replace("[DRAW]", "").strip()
            
            prompt = random.choice(COLUMBINA_IMAGE_PROMPTS)
            encoded_prompt = urllib.parse.quote(prompt)
            seed = random.randint(1, 100000)
            image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=512&height=512&seed={seed}&nologo=true&model=nano-banana"
            
            # 이미지 설명 추가 (선택사항)
            # columbina_reply += "\n(그림을 건네주며...)"

        columbina_chat_history[user_id].append({"user": message, "columbina": columbina_reply})
        
        # 산드로네 난입 확률 (30% -> 15% 하향 조정)
        rand_val = random.random()
        print(f"[Chatbot] Sandrone Check: {rand_val:.2f} < 0.15?")
        
        if rand_val < 0.15:
            try:
                print(f"[Chatbot] Sandrone Triggered!")
                sandrone_prompt = SANDRONE_INTERRUPT_PROMPT.format(columbina_reply=columbina_reply)
                sandrone_response = await gemini_model.generate_content_async(sandrone_prompt)
                sandrone_reply = sandrone_response.text.strip()
            except Exception as e:
                print(f"[Chatbot] Sandrone Error: {e}")
        
        return (columbina_reply, sandrone_reply, image_url)
    except Exception as e:
        print(f"[Chatbot] Columbina Error: {e}")
        return ("후후, 잠시 후에 다시 말해줘~", None, None)



async def chat_with_katherine(user_id: str, message: str) -> str:
    if not gemini_model:
        return "API 키가 설정되지 않았어요!"
    
    can_proceed, wait_time = await gemini_limiter.acquire()
    if not can_proceed:
        return f"잠시만요, 모험가님! {int(wait_time)}초 후에 다시 말씀해주세요~"
    
    if user_id not in katherine_chat_history:
        katherine_chat_history[user_id] = []
    
    history = katherine_chat_history[user_id]
    
    context = KATHERINE_SYSTEM_PROMPT + "\n\n최근 대화:\n"
    for msg in history[-5:]:
        context += f"모험가: {msg['user']}\n캐서린: {msg['katherine']}\n"
    
    context += f"\n모험가: {message}\n캐서린:"
    
    try:
        print(f"[Chatbot] Katherine: Sending request...")
        response = await gemini_model.generate_content_async(context)
        reply = response.text.strip()
        
        history.append({"user": message, "katherine": reply})
        if len(history) > 10:
            history.pop(0)
        
        return reply
    except Exception as e:
        print(f"[Chatbot] Katherine Error: {e}")
        return "죄송해요, 잠시 후에 다시 말씀해주세요~"

class Chatbot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="푸리나", description="푸리나와 대화해요")
    @app_commands.describe(말="푸리나에게 할 말")
    async def slash_furina(self, interaction: discord.Interaction, 말: str):
        await interaction.response.defer()
        user_id = str(interaction.user.id)
        reply = await chat_with_furina(user_id, 말)
        
        embed = discord.Embed(title="💧 푸리나", description=reply, color=0x4FC3F7)
        embed.set_footer(text=f"대화: {interaction.user.display_name}")
        await interaction.followup.send(embed=embed)
    
    @commands.command(name="푸리나")
    async def furina_chat(self, ctx, *, 말: str = None):
        if not 말:
            await ctx.send("뭐라고 말할지 적어줘! 예: `!푸리나 안녕`")
            return
        
        async with ctx.typing():
            user_id = str(ctx.author.id)
            reply = await chat_with_furina(user_id, 말)
        
        embed = discord.Embed(title="💧 푸리나", description=reply, color=0x4FC3F7)
        embed.set_footer(text=f"대화: {ctx.author.display_name}")
        await ctx.send(embed=embed)
    
    @commands.command(name="푸리나리셋")
    async def furina_reset(self, ctx):
        user_id = str(ctx.author.id)
        if user_id in furina_chat_history:
            del furina_chat_history[user_id]
        await ctx.send("💧 푸리나와의 대화 기록이 초기화되었어요!")
    
    @app_commands.command(name="콜롬비나", description="콜롬비나와 대화해요")
    @app_commands.describe(말="콜롬비나에게 할 말")
    async def slash_columbina(self, interaction: discord.Interaction, 말: str):
        await interaction.response.defer()
        user_id = str(interaction.user.id)
        columbina_reply, sandrone_reply, image_url = await chat_with_columbina(user_id, 말)
        
        embed = discord.Embed(title="🕊️ 콜롬비나", description=columbina_reply, color=0x9966CC)
        if image_url:
            embed.set_image(url=image_url)
        embed.set_footer(text=f"대화: {interaction.user.display_name}")
        await interaction.followup.send(embed=embed)
        
        if sandrone_reply:
            sandrone_embed = discord.Embed(title="🔧 산드로네", description=sandrone_reply, color=0x607D8B)
            await interaction.channel.send(embed=sandrone_embed)
    
    @commands.command(name="콜롬비나")
    async def columbina_chat(self, ctx, *, 말: str = None):
        if not 말:
            await ctx.send("뭐라고 말할지 적어줘! 예: `!콜롬비나 안녕`")
            return
        
        async with ctx.typing():
            user_id = str(ctx.author.id)
            columbina_reply, sandrone_reply, image_url = await chat_with_columbina(user_id, 말)
        
        embed = discord.Embed(title="🕊️ 콜롬비나", description=columbina_reply, color=0x9966CC)
        if image_url:
            embed.set_image(url=image_url)
        embed.set_footer(text=f"대화: {ctx.author.display_name}")
        await ctx.send(embed=embed)
        
        if sandrone_reply:
            sandrone_embed = discord.Embed(title="🔧 산드로네", description=sandrone_reply, color=0x607D8B)
            await ctx.send(embed=sandrone_embed)
    
    @commands.command(name="콜롬비나리셋")
    async def columbina_reset(self, ctx):
        user_id = str(ctx.author.id)
        if user_id in columbina_chat_history:
            del columbina_chat_history[user_id]
        if user_id in columbina_repeat_count:
            del columbina_repeat_count[user_id]
        await ctx.send("🕊️ 콜롬비나와의 대화 기록이 초기화되었어요!")
    
    @app_commands.command(name="캐서린", description="캐서린과 대화해요")
    @app_commands.describe(말="캐서린에게 할 말")
    async def slash_katherine(self, interaction: discord.Interaction, 말: str):
        await interaction.response.defer()
        user_id = str(interaction.user.id)
        reply = await chat_with_katherine(user_id, 말)
        
        embed = discord.Embed(title="🌟 캐서린", description=reply, color=0x98FB98)
        embed.set_footer(text=f"대화: {interaction.user.display_name}")
        await interaction.followup.send(embed=embed)
    
    @commands.command(name="캐서린")
    async def katherine_chat(self, ctx, *, 말: str = None):
        if not 말:
            await ctx.send("뭐라고 말할지 적어줘! 예: `!캐서린 안녕`")
            return
        
        async with ctx.typing():
            user_id = str(ctx.author.id)
            reply = await chat_with_katherine(user_id, 말)
        
        embed = discord.Embed(title="🌟 캐서린", description=reply, color=0x98FB98)
        embed.set_footer(text=f"대화: {ctx.author.display_name}")
        await ctx.send(embed=embed)
    
    @commands.command(name="캐서린리셋")
    async def katherine_reset(self, ctx):
        user_id = str(ctx.author.id)
        if user_id in katherine_chat_history:
            del katherine_chat_history[user_id]
        await ctx.send("🌟 캐서린과의 대화 기록이 초기화되었어요!")

async def setup(bot):
    await bot.add_cog(Chatbot(bot))
