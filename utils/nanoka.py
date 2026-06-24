"""
nanoka.cc (구 hakush.in) 데이터 API 헬퍼.

hakush.in 사이트가 폐쇄된 뒤 동일 데이터가 static.nanoka.cc 로 부활했다.
URL 구조가 바뀌었고(버전 세그먼트 추가), 응답 JSON 키도 소문자 스키마로 변경됨.

▶ 사이트가 또 옮겨가면 이 파일의 BASE_URL / 경로 규칙만 고치면 된다.
  각 cog 는 직접 URL 을 만들지 않고 여기 함수만 호출한다.
"""
import time
import aiohttp

BASE_URL = "https://static.nanoka.cc"
MANIFEST_URL = f"{BASE_URL}/manifest.json"

LANG = "ko"

# 게임별 "무기류" 엔드포인트 이름. manifest 의 new 키와 데이터 경로 모두 이 이름을 쓴다.
WEAPON_ENDPOINT = {"gi": "weapon", "hsr": "lightcone", "zzz": "weapon"}
# 게임별 "성유물류" 엔드포인트 이름.
ARTIFACT_ENDPOINT = {"gi": "artifact", "hsr": "relicset", "zzz": "equipment"}

# manifest["{game}"]["new"] 안의 키들
NEW_CHAR_KEY = "character"
NEW_ARTIFACT_KEY = ARTIFACT_ENDPOINT

# manifest 는 버전 정보가 자주 안 바뀌므로 프로세스 전역으로 캐싱한다.
_manifest_cache = {"data": None, "ts": 0.0}
_MANIFEST_TTL = 3600  # 1시간


async def fetch_manifest(session: aiohttp.ClientSession, *, force: bool = False) -> dict | None:
    """전체 manifest.json 을 가져온다(캐싱). 게임별 latest 버전과 신규 ID 목록을 담고 있다."""
    now = time.time()
    if not force and _manifest_cache["data"] and now - _manifest_cache["ts"] < _MANIFEST_TTL:
        return _manifest_cache["data"]
    try:
        async with session.get(MANIFEST_URL, timeout=aiohttp.ClientTimeout(total=15)) as resp:
            if resp.status == 200:
                data = await resp.json()
                _manifest_cache["data"] = data
                _manifest_cache["ts"] = now
                return data
    except Exception as e:
        print(f"[nanoka] manifest 요청 실패: {e}")
    # 실패 시 직전 캐시라도 반환(있으면)
    return _manifest_cache["data"]


async def get_version(session: aiohttp.ClientSession, game_key: str) -> str | None:
    """게임의 최신(latest) 데이터 버전 문자열을 반환. URL 경로에 끼워 넣는 용도."""
    manifest = await fetch_manifest(session)
    if not manifest:
        return None
    return manifest.get(game_key, {}).get("latest")


def weapon_list_url(game_key: str, version: str) -> str:
    """무기/광추 전체 목록 JSON (id -> 간단정보)."""
    return f"{BASE_URL}/{game_key}/{version}/{WEAPON_ENDPOINT[game_key]}.json"


def weapon_detail_url(game_key: str, version: str, weapon_id) -> str:
    """무기/광추 상세 JSON (한국어)."""
    return f"{BASE_URL}/{game_key}/{version}/{LANG}/{WEAPON_ENDPOINT[game_key]}/{weapon_id}.json"


def char_list_url(game_key: str, version: str) -> str:
    """캐릭터 전체 목록 JSON (id -> 간단정보)."""
    return f"{BASE_URL}/{game_key}/{version}/character.json"


def char_detail_url(game_key: str, version: str, char_id) -> str:
    """캐릭터 상세 JSON (한국어)."""
    return f"{BASE_URL}/{game_key}/{version}/{LANG}/character/{char_id}.json"


def artifact_list_url(game_key: str, version: str) -> str:
    """성유물/유물/디스크 전체 목록 JSON. 세트 효과까지 이 목록에 들어있다."""
    return f"{BASE_URL}/{game_key}/{version}/{ARTIFACT_ENDPOINT[game_key]}.json"


def site_url(game_key: str) -> str:
    """사람이 보는 웹사이트 주소 (예: https://gi.nanoka.cc/)."""
    return f"https://{game_key}.nanoka.cc/"


def _basename(path: str) -> str:
    """'Assets/.../Foo.png' 또는 'Foo' -> 'Foo' (경로/확장자 제거)."""
    return path.rsplit("/", 1)[-1].rsplit(".", 1)[0]


# ─────────────────────────────────────────────────────────────
# 아이콘 / 일러스트 URL
#   nanoka 자체 이미지 호스팅(static.nanoka.cc/.../UI)은 현재 비활성이라
#   안정적인 외부 CDN(Enka / Yatta)을 사용한다. 미출시 베타 항목은 CDN 에
#   아직 이미지가 없어 404 일 수 있으나(=썸네일 미표시), 크래시는 없다.
# ─────────────────────────────────────────────────────────────

def weapon_icon_url(game_key: str, *, icon: str | None = None, weapon_id=None) -> str | None:
    """무기/광추/음동기 아이콘 URL."""
    if game_key == "gi" and icon:
        return f"https://enka.network/ui/{icon}.png"
    if game_key == "zzz" and icon:
        return f"https://enka.network/ui/zzz/{_basename(icon)}.png"
    if game_key == "hsr" and weapon_id is not None:
        return f"https://sr.yatta.moe/hsr/assets/UI/equipment/medium/{weapon_id}.png"
    return None


def char_icon_url(game_key: str, *, icon: str | None = None, char_id=None) -> str | None:
    """캐릭터 얼굴 아이콘(썸네일) URL."""
    if game_key == "gi" and icon:
        return f"https://enka.network/ui/{icon}.png"
    if game_key == "zzz" and icon:
        return f"https://enka.network/ui/zzz/{_basename(icon)}.png"
    if game_key == "hsr" and char_id is not None:
        return f"https://sr.yatta.moe/hsr/assets/UI/avatar/medium/{char_id}.png"
    return None


def char_illustration_url(game_key: str, *, icon: str | None = None, char_id=None) -> str | None:
    """캐릭터 일러스트(풀 아트) URL.

    ZZZ 는 nanoka 가 직접 호스팅하는 마인드스케이프(6돌파/M6) 일러를 쓴다.
    GI/HSR 은 nanoka /assets/ 에 없어 외부 CDN(Enka 가챠아트 / Yatta 풀아트) 사용.
    미출시 베타 캐릭터는 어느 소스에도 일러가 없어 404(=미표시)일 수 있음.
    """
    if game_key == "gi" and icon:
        # 'UI_AvatarIcon_Ayaka' -> 'UI_Gacha_AvatarImg_Ayaka'
        name = icon.replace("UI_AvatarIcon_", "")
        return f"https://enka.network/ui/UI_Gacha_AvatarImg_{name}.png"
    if game_key == "hsr" and char_id is not None:
        return f"https://sr.yatta.moe/hsr/assets/UI/avatar/large/{char_id}.png"
    if game_key == "zzz" and char_id is not None:
        # 마인드스케이프 시네마 3단계(M6) 풀 일러. (1=기본, 2=각성, 3=M6)
        return f"{BASE_URL}/assets/zzz/Mindscape_{char_id}_3.webp"
    return None


def artifact_icon_url(game_key: str, icon: str | None) -> str | None:
    """성유물/유물/디스크 아이콘 URL."""
    if not icon:
        return None
    if game_key == "gi":
        return f"https://enka.network/ui/{icon}.png"
    if game_key == "hsr":
        # 'SpriteOutput/ItemIcon/71000.png' -> '71000'
        return f"https://sr.yatta.moe/hsr/assets/UI/relic/{_basename(icon)}.png"
    if game_key == "zzz":
        return f"https://enka.network/ui/zzz/{_basename(icon)}.png"
    return None
