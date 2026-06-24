import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

TEST_CHANNEL_ID = 0
GAME_CHANNEL_ID = 0

DATA_FILE = "data/user_data.json"
SENT_CODES_FILE = "data/sent_codes.json"
GUILD_SETTINGS_FILE = "data/guild_settings.json"
UID_DATA_FILE = "data/uid_data.json"
SENT_VIDEOS_FILE = "data/sent_videos.json"

HOYO_GAME_CONFIGS = {
    "genshin": {
        "channel_id": 0,
        "api_url": "https://hoyo-codes.seria.moe/codes?game=genshin",
        "redeem_url": "https://genshin.hoyoverse.com/ko/gift?code=",
        "name": "원신",
        "currency_keyword": "primogem",
        "currency_name": "원석",
    },
    "hkrpg": {
        "channel_id": 0,
        "api_url": "https://hoyo-codes.seria.moe/codes?game=hkrpg",
        "redeem_url": "https://hsr.hoyoverse.com/gift?code=",
        "name": "붕괴: 스타레일",
        "currency_keyword": "stellar jade",
        "currency_name": "성옥",
    },
    "nap": {
        "channel_id": 0,
        "api_url": "https://hoyo-codes.seria.moe/codes?game=nap",
        "redeem_url": "https://zenless.hoyoverse.com/redemption?code=",
        "name": "젠레스 존 제로",
        "currency_keyword": "polychrome",
        "currency_name": "폴리크롬",
    }
}

WUWA_CONFIG = {
    "channel_id": 0,
    "wiki_url": "https://wutheringwaves.fandom.com/wiki/Redemption_Code",
    "name": "명조",
    "currency_keyword": "astrite",
    "currency_name": "성정",
}

ENDFIELD_CONFIG = {
    "url": "https://game8.co/games/Arknights-Endfield/archives/571509",
    "name": "명일방주: 엔드필드",
    "currency_keyword": "oroberyl",
    "currency_name": "오로베릴",
}

YOUTUBE_CHANNELS = {
    "genshin_yt": {
        "channel_id": "UCcum1rCJ5GJeQ_xv0xrohqg",
        "name": "원신",
        "emoji": "🌟"
    },
    "starrail_yt": {
        "channel_id": "UCH33CJMcI0XZUpIhWRHiUuw",
        "name": "스타레일",
        "emoji": "🚂"
    },
    "zzz_yt": {
        "channel_id": "UCmry1hfaRHI_iTfxUMhC8mA",
        "name": "젠레스",
        "emoji": "📺"
    },
    "wuwa_yt": {
        "channel_id": "UCKuq0c-RXYaulECSuu5hFug",
        "name": "명조",
        "emoji": "🌊"
    },
    "petitplanet_yt": {
        "channel_id": "UC5Qv07LfJfNHQGDfSjalw2Q",
        "name": "쁘띠플레닛",
        "emoji": "🎮"
    },
    "varsapura_yt": {
        "channel_id": "UC0S7mjW7Rjh2TYFJouHduBg",
        "name": "Varsapura",
        "emoji": "🎬"
    },
    "nexusanima_yt": {
        "channel_id": "UCR_M7m-eF0cXa3nrdNHsp6g",
        "name": "넥서스아니마",
        "emoji": "💫"
    },
    "endfield_yt": {
        "channel_id": "UCIf9gYpmmIJV7flBhUhuqYQ",
        "name": "엔드필드",
        "emoji": "🏗️"
    }
}

YOUTUBE_SEARCH_API = "https://www.googleapis.com/youtube/v3/search"
YOUTUBE_VIDEO_API = "https://www.googleapis.com/youtube/v3/videos"

CHARACTER_FORTUNES = [
    ("콜롬비나", "😴", "하루 종일 졸음이 쏟아집니다... 침대의 유혹을 이길 수 없을지도?", 0x9966CC),
    ("마비카", "🔥", "열받는 일이 생길지도 모릅니다. 그래도 불의 신처럼 참으세요.", 0xFF4500),
    ("푸리나", "🎭", "누군가의 연기에 속을 수 있습니다. 달콤한 말 조심하세요!", 0x4169E1),
    ("나히다", "🌸", "꽃마차가 덜컹거리는 것처럼, 작은 해프닝이 있을 수 있어요.", 0x98FB98),
    ("라이덴", "⚡", "영원히 이불 속에 있고 싶은 날입니다. 휴식이 필요해요.", 0x8A2BE2),
    ("종려", "🪨", "지갑을 집에 두고 왔나요? 오늘은 충동구매를 조심하세요.", 0xDAA520),
    ("벤티", "🍃", "바람이 이끄는 대로~ 중요한 일은 내일의 나에게 미루게 됩니다.", 0x7FFFD4),
    ("베넷", "🍀", "운이 조금 없을 수도... 하지만 따봉 하나면 극복 가능합니다!", 0x32CD32),
    ("니콜", "🕊️", "말보다 마음의 소리에 귀 기울이는 날. 침묵 속에서 진심이 전해질지도.", 0xFF6B35),
    ("산드로네", "🤖", "감정을 배제하고 기계처럼 효율적으로 처리하면 성공하는 날.", 0x708090),
    ("느비예트", "🌧️", "오늘 하루 물 2리터 마시기 도전! 물의 용왕님이 지켜보고 계십니다.", 0x1E90FF),
    ("야에 미코", "🦊", "재미있는 구경거리가 생길지도? 여유롭게 즐기세요~", 0xFF69B4),
    ("치치", "🧟", "어라... 뭘 하려고 했더라? 메모하는 습관이 필요한 날.", 0xE6E6FA),
    ("요이미야", "🎆", "폭죽처럼 팡! 터지는 활기찬 하루가 될 거예요!", 0xFFD700),
    ("아를레키노", "🔥", "차가운 이성으로 결단할 때입니다. 망설임은 금물.", 0x8B0000),
    ("파루잔", "📖", "지식의 탐구에 좋은 날입니다! 선배님이라고 불러보세요.", 0x20B2AA),
    ("코코미", "🐟", "모든 것이 책략대로. 준비된 자에게 완벽한 승리가 찾아옵니다.", 0xFFB6C1),
    ("시틀라리", "👵", "「요즘 젊은것들은…」 잔소리 속에 노련한 지혜가 빛나는 날. 따뜻하게 입어.", 0x90CAF9),
    ("라우마", "🌙", "달빛처럼 은은한 위로가 찾아오는 날. 지친 마음에 숲의 축복이 깃듭니다.", 0x66BB6A),
]

NOTIFY_TYPES = {
    "genshin": {"name": "원신 코드", "emoji": "🌟"},
    "hkrpg": {"name": "스타레일 코드", "emoji": "🚂"},
    "nap": {"name": "젠레스 코드", "emoji": "📺"},
    "wuwa": {"name": "명조 코드", "emoji": "🌊"},
    "endfield": {"name": "엔드필드 코드", "emoji": "🏗️"},
    "genshin_yt": {"name": "원신 유튜브", "emoji": "🎬"},
    "starrail_yt": {"name": "스타레일 유튜브", "emoji": "🎬"},
    "zzz_yt": {"name": "젠레스 유튜브", "emoji": "🎬"},
    "wuwa_yt": {"name": "명조 유튜브", "emoji": "🎬"},
    "endfield_yt": {"name": "엔드필드 유튜브", "emoji": "🎬"},
    "petitplanet_yt": {"name": "쁘띠플레닛", "emoji": "🎮"},
    "varsapura_yt": {"name": "Varsapura", "emoji": "🎬"},
    "nexusanima_yt": {"name": "넥서스아니마", "emoji": "💫"},
    "genshin_yt_community": {"name": "원신 커뮤니티", "emoji": "📢"},
    "starrail_yt_community": {"name": "스타레일 커뮤니티", "emoji": "📢"},
    "zzz_yt_community": {"name": "젠레스 커뮤니티", "emoji": "📢"},
    "wuwa_yt_community": {"name": "명조 커뮤니티", "emoji": "📢"},
    "endfield_yt_community": {"name": "엔드필드 커뮤니티", "emoji": "📢"},
    "petitplanet_yt_community": {"name": "쁘띠플레닛 커뮤니티", "emoji": "📢"},
    "varsapura_yt_community": {"name": "Varsapura 커뮤니티", "emoji": "📢"},
    "nexusanima_yt_community": {"name": "넥서스아니마 커뮤니티", "emoji": "📢"},
    "hakushin_update": {"name": "신규 업데이트", "emoji": "🆕"},
}

SENT_HAKUSHIN_FILE = "data/sent_hakushin.json"

CHARACTER_NAME_TO_ENKA = {
    "콜롬비나": "Columbina", "푸리나": "Furina", "나히다": "Nahida",
    "라이덴": "Raiden Shogun", "종려": "Zhongli", "벤티": "Venti",
    "카즈하": "Kaedehara Kazuha", "야에미코": "Yae Miko", "호두": "Hu Tao",
    "감우": "Ganyu", "아야카": "Kamisato Ayaka", "닐루": "Nilou",
    "방랑자": "Wanderer", "알하이탐": "Alhaitham", "느비예트": "Neuvillette",
    "클로린드": "Clorinde", "아를레키노": "Arlecchino", "나비아": "Navia",
    "시그윈": "Sigewinne", "치오리": "Chiori", "마비카": "Mavuika",
    "사이노": "Cyno", "타이나리": "Tighnari", "데히야": "Dehya",
    "각청": "Keqing", "모나": "Mona", "진": "Jean", "다이루크": "Diluc",
    "치치": "Qiqi", "클레": "Klee", "타르탈리아": "Tartaglia",
    "알베도": "Albedo", "소": "Xiao", "유라": "Eula", "카미사토 아야토": "Kamisato Ayato",
    "아야토": "Kamisato Ayato", "예란": "Yelan", "카에데하라 카즈하": "Kaedehara Kazuha",
    "쿠키 시노부": "Kuki Shinobu", "시노부": "Kuki Shinobu",
    "세노": "Cyno", "캔디스": "Candace", "도리": "Dori",
    "레이라": "Layla", "파루잔": "Faruzan", "스카라무슈": "Wanderer",
    "요이미야": "Yoimiya", "사유": "Sayu", "토마": "Thoma",
    "고로": "Gorou", "이토": "Arataki Itto", "아라타키 이토": "Arataki Itto",
    "키라라": "Kirara", "바이주": "Baizhu", "카베": "Kaveh",
    "린니": "Lyney", "리넷": "Lynette", "프레미네": "Freminet",
    "라이오슬리": "Wriothesley", "샤를로트": "Charlotte",
}

AVATAR_ID_TO_KR = {
    10000002: "아야카", 10000003: "진", 10000005: "여행자(남)", 10000006: "리사",
    10000007: "여행자(여)", 10000014: "바바라", 10000015: "케이아", 10000016: "다이루크",
    10000020: "레이저", 10000021: "엠버", 10000022: "벤티", 10000023: "향릉",
    10000024: "북두", 10000025: "행추", 10000026: "소", 10000027: "응광",
    10000029: "클레", 10000030: "종려", 10000031: "피슬", 10000032: "베넷",
    10000033: "타르탈리아", 10000034: "노엘", 10000035: "치치", 10000036: "중운",
    10000037: "감우", 10000038: "알베도", 10000039: "설탕", 10000041: "모나",
    10000042: "각청", 10000043: "디오나", 10000044: "신염", 10000045: "로자리아",
    10000046: "호두", 10000047: "카즈하", 10000048: "연비", 10000049: "요이미야",
    10000050: "토마", 10000051: "유라", 10000052: "라이덴 쇼군", 10000053: "사유",
    10000054: "코코미", 10000055: "고로", 10000056: "사라", 10000057: "이토",
    10000058: "야에 미코", 10000059: "시카노인 헤이조", 10000060: "야란", 10000062: "에일로이",
    10000063: "신학", 10000064: "운근", 10000065: "쿠키 시노부", 10000066: "아야토",
    10000067: "콜레이", 10000068: "도리", 10000069: "타이나리", 10000070: "닐루",
    10000071: "사이노", 10000072: "캔디스", 10000073: "나히다", 10000074: "레일라",
    10000075: "방랑자", 10000076: "파루잔", 10000077: "요요", 10000078: "알하이탐",
    10000079: "데히야", 10000080: "미카", 10000081: "카베", 10000082: "백출",
    10000083: "키라라", 10000084: "리니", 10000085: "리넷", 10000086: "프레미네",
    10000087: "느비예트", 10000088: "라이오슬리", 10000089: "샤를로트",
    10000090: "슈브루즈", 10000091: "나비아", 10000092: "가명", 10000093: "한운",
    10000094: "치오리", 10000095: "시그윈", 10000096: "아를레키노", 10000097: "세토스",
    10000098: "클로린드", 10000099: "에밀리", 10000100: "카치나", 10000101: "키니치",
    10000102: "말라니", 10000103: "실로닌", 10000104: "차스카", 10000105: "오로론",
    10000106: "마비카", 10000107: "시틀라리", 10000108: "란얀", 10000109: "미즈키",
    10000110: "이안산", 10000111: "바레사", 10000112: "에스코피에", 10000113: "이파",
    10000114: "스커크", 10000115: "달리아", 10000116: "이네파",
    10000117: "별인형", 10000118: "별인형",
    10000119: "라우마", 10000120: "플린스", 10000121: "아이노", 10000122: "네페르",
    10000123: "두린", 10000124: "야호다",
    10000904: "콜롬비나",
}

AVATAR_ICON_NAMES = {
    10000002: "Ayaka", 10000003: "Qin", 10000006: "Lisa", 10000014: "Barbara",
    10000015: "Kaeya", 10000016: "Diluc", 10000020: "Razor", 10000021: "Ambor",
    10000022: "Venti", 10000023: "Xiangling", 10000024: "Beidou", 10000025: "Xingqiu",
    10000026: "Xiao", 10000027: "Ningguang", 10000029: "Klee", 10000030: "Zhongli",
    10000031: "Fischl", 10000032: "Bennett", 10000033: "Tartaglia", 10000034: "Noel",
    10000035: "Qiqi", 10000036: "Chongyun", 10000037: "Ganyu", 10000038: "Albedo",
    10000039: "Sucrose", 10000041: "Mona", 10000042: "Keqing", 10000043: "Diona",
    10000044: "Xinyan", 10000045: "Rosaria", 10000046: "Hutao", 10000047: "Kazuha",
    10000048: "Feiyan", 10000049: "Yoimiya", 10000050: "Tohma", 10000051: "Eula",
    10000052: "Shougun", 10000053: "Sayu", 10000054: "Kokomi", 10000055: "Gorou",
    10000056: "Sara", 10000057: "Itto", 10000058: "Yae", 10000059: "Heizo",
    10000060: "Yelan", 10000063: "Shenhe", 10000064: "Yunjin", 10000065: "Shinobu",
    10000066: "Ayato", 10000067: "Collei", 10000068: "Dori", 10000069: "Tighnari",
    10000070: "Nilou", 10000071: "Cyno", 10000072: "Candace", 10000073: "Nahida",
    10000074: "Layla", 10000075: "Wanderer", 10000076: "Faruzan", 10000077: "Yaoyao",
    10000078: "Alhatham", 10000079: "Dehya", 10000080: "Mika", 10000081: "Kaveh",
    10000082: "Baizhu", 10000083: "Kirara", 10000084: "Lyney", 10000085: "Lynette",
    10000086: "Freminet", 10000087: "Neuvillette", 10000088: "Wriothesley",
    10000089: "Charlotte", 10000090: "Chevreuse", 10000091: "Navia", 10000092: "Gaming",
    10000093: "Liuyun", 10000094: "Chiori", 10000095: "Sigewinne", 10000096: "Arlecchino",
    10000097: "Sethos", 10000098: "Clorinde", 10000099: "Emilie", 10000100: "Kachina",
    10000101: "Kinich", 10000102: "Mualani", 10000103: "Xilonen", 10000104: "Chasca",
    10000105: "Olorun", 10000106: "Mavuika", 10000107: "Citlali", 10000108: "Lanyan",
    10000109: "Mizuki", 10000110: "Iansan", 10000111: "Varesa", 10000112: "Escoffier",
    10000119: "Lauma", 10000120: "Flins", 10000121: "Aino", 10000122: "Nefer",
    10000904: "Columbina",
}

COSTUME_ART_NAMES = {
    200301: "QinCostumeSea", 200302: "QinCostumeWic",
    200201: "AyakaCostumeFruhling", 200601: "LisaCostumeStudentin",
    201401: "BarbaraCostumeSummertime", 201501: "KaeyaCostumeDancer",
    201601: "DilucCostumeFlamme", 202101: "AmborCostumeWic",
}

ELEMENT_COLORS = {
    "Fire": 0xFF6B35, "Water": 0x4FC3F7, "Wind": 0x81C784,
    "Electric": 0xBA68C8, "Ice": 0x90CAF9, "Rock": 0xFFD54F,
    "Grass": 0x66BB6A,
}

ELEMENT_KR = {
    "Fire": "불", "Water": "물", "Wind": "바람", "Electric": "번개",
    "Ice": "얼음", "Rock": "바위", "Grass": "풀",
}

STAT_KR = {
    2000: ("HP", ""), 2001: ("공격력", ""), 2002: ("방어력", ""),
    28: ("원소 마스터리", ""), 20: ("치명타 확률", "%"), 22: ("치명타 피해", "%"),
    23: ("원충", "%"), 30: ("물리 피해 보너스", "%"),
    40: ("불 원소 피해", "%"), 41: ("번개 원소 피해", "%"),
    42: ("물 원소 피해", "%"), 43: ("풀 원소 피해", "%"),
    44: ("바람 원소 피해", "%"), 45: ("바위 원소 피해", "%"),
    46: ("얼음 원소 피해", "%"), 26: ("치유 보너스", "%"),
}
