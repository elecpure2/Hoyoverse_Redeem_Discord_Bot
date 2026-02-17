"""
Prydwen.gg 젠레스 존 제로(Zenless Zone Zero) 데이터 모듈
에이전트, W-엔진, 드라이브 디스크 정보를 Prydwen에서 가져옵니다.
"""
import aiohttp
import json
import re
from typing import Dict, Optional

BASE_API = "https://www.prydwen.gg/page-data/zenless"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

# ─── 한글 매핑 ─────────────────────────────────────────

ELEMENT_KO = {
    'Physical': '물리', 'Fire': '화염', 'Ice': '빙결', 'Electric': '전기',
    'Ether': '에테르',
}

STYLE_KO = {
    'Attack': '강공', 'Stun': '격동', 'Anomaly': '이상',
    'Defense': '방어', 'Defence': '방어', 'Support': '지원',
}

# 영어 이름 → 공식 한국어 이름
NAME_KO = {
    'Alice': '앨리스', 'Anby': '엔비', 'Anby: Soldier 0': '엔비: 솔저 0',
    'Anton': '앤톤', 'Aria': '아리아', 'Astra Yao': '아스트라 야오',
    'Banyue': '반월', 'Ben': '벤', 'Billy': '빌리',
    'Burnice': '버니스', 'Caesar': '시저',
    'Cissia': '시시아', 'Corin': '코린',
    'Dialyn': '디올린', 'Ellen': '엘렌', 'Evelyn': '이블린',
    'Grace': '그레이스', 'Harumasa': '하루마사', 'Hugo': '휴고',
    'Jane Doe': '제인 도', 'Ju Fufu': '주 푸푸',
    'Koleda': '콜레다', 'Lighter': '라이터', 'Lucia': '루시아', 'Lucy': '루시',
    'Lycaon': '라이칸', 'Manato': '마나토',
    'Miyabi': '미야비', 'Nangong Yu': '엽빛나',
    'Nekomata': '네코마타', 'Nicole': '니콜',
    'Orphie & Magus': '오르피 & 마구스', 'Pan Yinhu': '판 인후',
    'Piper': '파이퍼', 'Pulchra': '풀크라',
    'Qingyi': '청의', 'Rina': '리나',
    'Seed': '시드', 'Seth': '세스',
    'Soldier 11': '11호', 'Soukaku': '소우카쿠',
    'Sunna': '선나', 'Trigger': '트리거',
    'Vivian': '비비안', 'Yanagi': '야나기',
    'Ye Shunguang': '예 순광', 'Yidhari': '이드하리',
    'Yixuan': '이셴', 'Yuzuha': '유즈하', 'Zhao': '자오',
    'Zhu Yuan': '주원',
}



# ─── 유틸 ─────────────────────────────────────────

async def _fetch_page_data(session: aiohttp.ClientSession, path: str) -> Optional[dict]:
    """Prydwen page-data.json 가져오기"""
    url = f"{BASE_API}/{path}/page-data.json"
    try:
        async with session.get(url, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=15)) as resp:
            if resp.status != 200:
                return None
            data = json.loads(await resp.text())
            return data.get("result", {}).get("data", {})
    except Exception:
        return None


def _contentful_to_text(raw) -> str:
    """Contentful rich text → 평문"""
    if not raw:
        return ""
    if isinstance(raw, str):
        return re.sub(r'<[^>]+>', '', raw).strip()
    if isinstance(raw, dict) and 'raw' in raw:
        try:
            raw = json.loads(raw['raw'])
        except (json.JSONDecodeError, TypeError):
            return str(raw.get('raw', ''))

    def extract(node):
        if isinstance(node, str):
            return node
        if not isinstance(node, dict):
            return ""
        value = node.get("value", "")
        content = node.get("content", [])
        parts = [value] if value else []
        for child in content:
            parts.append(extract(child))
        text = "".join(parts)
        if node.get("nodeType") == "paragraph":
            return text + "\n"
        return text

    return extract(raw).strip()


def _clean_html(text: str) -> str:
    return re.sub(r'<[^>]+>', '', text).strip()


def _get_ko_name(en_name: str) -> str:
    return NAME_KO.get(en_name, en_name)


# ─── 에이전트 ─────────────────────────────────────────

async def fetch_agent_list(session: aiohttp.ClientSession) -> Dict[str, dict]:
    """에이전트 목록. {한글이름: {slug, name_en, rarity, element, style, faction}}"""
    data = await _fetch_page_data(session, "characters")
    if not data:
        return {}

    nodes = data.get("allCharacters", {}).get("nodes", [])
    result = {}
    for n in nodes:
        en_name = n.get("name", "")
        ko_name = _get_ko_name(en_name)
        result[ko_name] = {
            "slug": n.get("slug", ""),
            "name_en": en_name,
            "rarity": n.get("rarity", "A"),  # S or A
            "element": n.get("element", ""),
            "element_ko": ELEMENT_KO.get(n.get("element", ""), n.get("element", "")),
            "style": n.get("style", ""),
            "style_ko": STYLE_KO.get(n.get("style", ""), n.get("style", "")),
            "faction": n.get("faction", ""),
            "createdAt": n.get("createdAt", ""),
        }
    return result


async def fetch_agent_detail(session: aiohttp.ClientSession, slug: str) -> Optional[dict]:
    """에이전트 상세"""
    data = await _fetch_page_data(session, f"characters/{slug}")
    if not data:
        return None

    nodes = data.get("currentUnit", {}).get("nodes", [])
    if not nodes:
        return None

    u = nodes[0]
    en_name = u.get("name", slug)
    ko_name = _get_ko_name(en_name)

    # 마인드스케이프 시네마 (talents)
    talents = []
    for t in u.get("talents", []):
        desc = _clean_html(t.get("desc", ""))
        talents.append({"name": t.get("name", ""), "description": desc})

    # 소개
    intro = _contentful_to_text(u.get("introduction", {}))

    return {
        "name": ko_name,
        "name_en": en_name,
        "full_name": u.get("fullName", en_name),
        "slug": slug,
        "rarity": u.get("rarity", "A"),
        "element": u.get("element", ""),
        "element_ko": ELEMENT_KO.get(u.get("element", ""), ""),
        "style": u.get("style", ""),
        "style_ko": STYLE_KO.get(u.get("style", ""), ""),
        "faction": u.get("faction", ""),
        "introduction": intro,
        "talents": talents,
        "voice_kr": u.get("voiceActors", {}).get("kr", ""),
        "url": f"https://www.prydwen.gg/zenless/characters/{slug}",
    }


# ─── W-엔진 ─────────────────────────────────────────

async def fetch_wengine_list(session: aiohttp.ClientSession) -> Dict[str, dict]:
    """W-엔진 목록. {이름: {slug, rarity, element, type}}"""
    data = await _fetch_page_data(session, "w-engines")
    if not data:
        return {}

    nodes = data.get("allCharacters", {}).get("nodes", [])
    result = {}
    for n in nodes:
        name = n.get("name", "")
        result[name] = {
            "slug": name,  # W-엔진은 별도 상세 페이지 경로가 필요
            "name": name,
            "rarity": n.get("rarity", "A"),
            "talent_name": n.get("talentName", ""),
            "element": n.get("element", ""),
            "type": n.get("type", ""),
            "type_ko": STYLE_KO.get(n.get("type", ""), n.get("type", "")),
            "description": _contentful_to_text(n.get("description", {})),
            "stats": n.get("stats", {}),
            "createdAt": n.get("createdAt", ""),
        }
    return result


# ─── 드라이브 디스크 ─────────────────────────────────────

async def fetch_disk_list(session: aiohttp.ClientSession) -> Dict[str, dict]:
    """드라이브 디스크 세트 목록. {이름: {bonus2, bonus4}}"""
    # 여러 가능한 경로 시도
    for path in ["disk-drives", "guides/disk-drives", "guides/disk-drive-sets"]:
        data = await _fetch_page_data(session, path)
        if data:
            for key in data:
                val = data[key]
                if isinstance(val, dict) and "nodes" in val:
                    nodes = val["nodes"]
                    result = {}
                    for n in nodes:
                        name = n.get("name", "")
                        b2 = _contentful_to_text(n.get("bonus2", n.get("twoSet", {})))
                        b4 = _contentful_to_text(n.get("bonus4", n.get("fourSet", {})))
                        result[name] = {
                            "name": name,
                            "bonus2": b2,
                            "bonus4": b4,
                        }
                    if result:
                        return result
    return {}


# ─── 검색 유틸 ─────────────────────────────────────────

def search_items(query: str, item_dict: dict, limit: int = 10) -> list:
    """이름 검색 (부분 일치, 한/영 모두)"""
    query_lower = query.lower()

    exact = [(name, val) for name, val in item_dict.items() if name.lower() == query_lower]
    if exact:
        return exact

    for name, val in item_dict.items():
        if isinstance(val, dict) and val.get("name_en", "").lower() == query_lower:
            return [(name, val)]

    partial = []
    for name, val in item_dict.items():
        if query_lower in name.lower():
            partial.append((name, val))
        elif isinstance(val, dict) and query_lower in val.get("name_en", "").lower():
            partial.append((name, val))
        elif isinstance(val, dict) and query_lower in val.get("name", "").lower():
            partial.append((name, val))
    return partial[:limit]
