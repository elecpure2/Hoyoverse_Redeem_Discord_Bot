"""
Enka API 로컬라이제이션 데이터 관리 모듈
캐릭터 ID를 한글 이름으로 변환하는 기능 제공
"""
import aiohttp
import asyncio
import json
import os
import time
from typing import Optional, Dict, Any

from utils.config import AVATAR_ID_TO_KR

# 캐시 파일 경로
CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "cache")
CHARACTERS_CACHE = os.path.join(CACHE_DIR, "enka_characters.json")
LOCALE_CACHE = os.path.join(CACHE_DIR, "enka_locale_ko.json")
DIMBREATH_AVATAR_CACHE = os.path.join(CACHE_DIR, "dimbreath_avatar.json")
DIMBREATH_TEXTMAP_CACHE = os.path.join(CACHE_DIR, "dimbreath_textmap_kr.json")

# 캐시 만료 시간 (24시간)
CACHE_TTL = 24 * 60 * 60

# Enka API 데이터 URL
CHARACTERS_URL = "https://raw.githubusercontent.com/EnkaNetwork/API-docs/master/store/characters.json"
LOCALE_URL = "https://raw.githubusercontent.com/EnkaNetwork/API-docs/master/store/loc.json"

# Dimbreath 데이터 URL (최신 게임 데이터)
DIMBREATH_AVATAR_URL = "https://gitlab.com/Dimbreath/AnimeGameData/-/raw/master/ExcelBinOutput/AvatarExcelConfigData.json"
DIMBREATH_TEXTMAP_URL = "https://gitlab.com/Dimbreath/AnimeGameData/-/raw/master/TextMap/TextMapKR.json"

# 메모리 캐시
_characters_data: Dict[str, Any] = {}
_locale_data: Dict[str, str] = {}
_cache_loaded = False


def _ensure_cache_dir():
    """캐시 디렉토리 생성"""
    os.makedirs(CACHE_DIR, exist_ok=True)


def _is_cache_valid(cache_path: str) -> bool:
    """캐시 파일이 유효한지 확인"""
    if not os.path.exists(cache_path):
        return False
    
    file_mtime = os.path.getmtime(cache_path)
    return (time.time() - file_mtime) < CACHE_TTL


def _load_cache_from_file():
    """파일에서 캐시 로드"""
    global _characters_data, _locale_data, _cache_loaded
    
    try:
        if os.path.exists(CHARACTERS_CACHE):
            with open(CHARACTERS_CACHE, "r", encoding="utf-8") as f:
                _characters_data = json.load(f)
        
        if os.path.exists(LOCALE_CACHE):
            with open(LOCALE_CACHE, "r", encoding="utf-8") as f:
                _locale_data = json.load(f)
        
        if _characters_data and _locale_data:
            _cache_loaded = True
            return True
    except Exception as e:
        print(f"캐시 로드 실패: {e}")
    
    return False


def _save_cache_to_file():
    """캐시를 파일에 저장"""
    _ensure_cache_dir()
    
    try:
        with open(CHARACTERS_CACHE, "w", encoding="utf-8") as f:
            json.dump(_characters_data, f, ensure_ascii=False)
        
        with open(LOCALE_CACHE, "w", encoding="utf-8") as f:
            json.dump(_locale_data, f, ensure_ascii=False)
    except Exception as e:
        print(f"캐시 저장 실패: {e}")


async def refresh_locale_cache() -> bool:
    """Enka 로컬라이제이션 데이터 갱신"""
    global _characters_data, _locale_data, _cache_loaded
    
    try:
        async with aiohttp.ClientSession() as session:
            # characters.json 다운로드
            async with session.get(CHARACTERS_URL, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                if resp.status != 200:
                    print(f"캐릭터 데이터 다운로드 실패: HTTP {resp.status}")
                    return False
                _characters_data = await resp.json(content_type=None)
            
            # loc.json 다운로드 (한국어만 추출)
            async with session.get(LOCALE_URL, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                if resp.status != 200:
                    print(f"로컬 데이터 다운로드 실패: HTTP {resp.status}")
                    return False
                full_locale = await resp.json(content_type=None)
                _locale_data = full_locale.get("ko", {})
        
        # 파일에 저장
        _save_cache_to_file()
        _cache_loaded = True
        print(f"Enka 로컬 데이터 갱신 완료: {len(_characters_data)}개 캐릭터, {len(_locale_data)}개 번역")
        return True
        
    except Exception as e:
        print(f"Enka 로컬 데이터 갱신 중 오류: {e}")
        return False


async def _ensure_cache_loaded():
    """캐시가 로드되어 있는지 확인하고, 필요시 로드/갱신"""
    global _cache_loaded
    
    if _cache_loaded:
        return
    
    # 파일 캐시가 유효하면 로드
    if _is_cache_valid(CHARACTERS_CACHE) and _is_cache_valid(LOCALE_CACHE):
        if _load_cache_from_file():
            return
    
    # 캐시가 없거나 만료되었으면 갱신
    await refresh_locale_cache()
    
    # 그래도 로드 안 되었으면 파일에서라도 로드 시도
    if not _cache_loaded:
        _load_cache_from_file()


async def get_character_name_kr(avatar_id: int) -> str:
    """
    캐릭터 ID를 한글 이름으로 변환
    
    Args:
        avatar_id: 캐릭터 ID (예: 10000106)
    
    Returns:
        한글 캐릭터 이름 (예: "마비카")
        찾을 수 없으면 "캐릭터_{id}" 형식 반환
    """
    await _ensure_cache_loaded()
    
    fallback_name = f"캐릭터_{avatar_id}"
    
    # Enka 데이터에서 조회
    char_data = _characters_data.get(str(avatar_id), {})
    name_hash = char_data.get("NameTextMapHash")
    
    if name_hash:
        kr_name = _locale_data.get(str(name_hash))
        if kr_name:
            return kr_name
    
    # Enka 데이터에서 못 찾으면 로컬 딕셔너리 fallback
    local_name = AVATAR_ID_TO_KR.get(avatar_id)
    if local_name:
        return local_name
    
    return fallback_name


async def get_character_names_kr(avatar_ids: list) -> Dict[int, str]:
    """
    여러 캐릭터 ID를 한글 이름으로 변환
    
    Args:
        avatar_ids: 캐릭터 ID 목록
    
    Returns:
        {avatar_id: 한글이름} 딕셔너리
    """
    await _ensure_cache_loaded()
    
    result = {}
    for avatar_id in avatar_ids:
        result[avatar_id] = await get_character_name_kr(avatar_id)
    return result
