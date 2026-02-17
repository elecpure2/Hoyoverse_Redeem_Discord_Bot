"""
Prydwen.gg 스타레일(Honkai: Star Rail) 데이터 모듈
캐릭터, 광추, 유물 세트 정보를 Prydwen 페이지 데이터에서 가져옵니다.
한글 이름은 StarRailRes(게임 데이터)에서 자동으로 가져옵니다.
"""
import aiohttp
import json
import re
from typing import Dict, List, Optional, Tuple

BASE_API = "https://www.prydwen.gg/page-data/star-rail"
_SRR = "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/index_min/kr"
SRR_URLS = {
    "characters": f"{_SRR}/characters.json",
    "skills": f"{_SRR}/character_skills.json",
    "ranks": f"{_SRR}/character_ranks.json",
    "skill_trees": f"{_SRR}/character_skill_trees.json",
    "light_cones": f"{_SRR}/light_cones.json",
    "lc_ranks": f"{_SRR}/light_cone_ranks.json",
    "relic_sets": f"{_SRR}/relic_sets.json",
}
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

# ─── 한글 매핑 ─────────────────────────────────────────

ELEMENT_KO = {
    'Physical': '물리', 'Fire': '화염', 'Ice': '빙결', 'Lightning': '번개',
    'Wind': '바람', 'Quantum': '양자', 'Imaginary': '허수',
}

PATH_KO = {
    'Destruction': '파멸', 'Hunt': '순행', 'Erudition': '지혜',
    'Harmony': '조화', 'Nihility': '허무', 'Abundance': '풍요',
    'Preservation': '존호', 'Remembrance': '기억', 'Elation': '환락',
}

# ─── StarRailRes 한글 캐시 (봇 시작 시 로드) ────────────────
_TAG_TO_KO: Dict[str, str] = {}      # tag → 한글 이름
_CHAR_ID_BY_TAG: Dict[str, str] = {} # tag → character id
_SKILLS_KO: Dict[str, dict] = {}     # skill_id → {name, type_text, desc, ...}
_RANKS_KO: Dict[str, dict] = {}      # rank_id → {name, desc}
_LC_KO: Dict[str, dict] = {}         # lc_id → {name, desc, path, rarity}
_LC_RANKS_KO: Dict[str, dict] = {}   # lc_id → {skill, ...}
_RELIC_SETS_KO: Dict[str, dict] = {} # set_id → {name, desc[]}

_SPECIAL_KO = {
    'playerboy': '개척자', 'playergirl': '개척자',
    'playerboy2': '개척자', 'playergirl2': '개척자',
    'playerboy3': '개척자', 'playergirl3': '개척자',
    'playerboy4': '개척자', 'playergirl4': '개척자',
}


async def _fetch_json(session: aiohttp.ClientSession, url: str) -> Optional[dict]:
    """GitHub raw JSON 가져오기"""
    try:
        async with session.get(url, headers=HEADERS,
                               timeout=aiohttp.ClientTimeout(total=20)) as resp:
            if resp.status != 200:
                return None
            return json.loads(await resp.text())
    except Exception:
        return None


async def load_kr_data(session: aiohttp.ClientSession) -> bool:
    """StarRailRes에서 모든 한글 데이터 로드. 봇 시작 시 1회 호출."""
    global _TAG_TO_KO, _CHAR_ID_BY_TAG, _SKILLS_KO, _RANKS_KO
    global _LC_KO, _LC_RANKS_KO, _RELIC_SETS_KO

    # 캐릭터 이름
    chars = await _fetch_json(session, SRR_URLS["characters"])
    if chars:
        for cid, info in chars.items():
            tag = info.get("tag", "")
            name = info.get("name", "")
            if tag and name and name != "{NICKNAME}":
                _TAG_TO_KO[tag.lower()] = name
                _CHAR_ID_BY_TAG[tag.lower()] = cid
        _TAG_TO_KO.update(_SPECIAL_KO)

    # 스킬
    skills = await _fetch_json(session, SRR_URLS["skills"])
    if skills:
        _SKILLS_KO.update(skills)

    # 에이도론 (ranks)
    ranks = await _fetch_json(session, SRR_URLS["ranks"])
    if ranks:
        _RANKS_KO.update(ranks)

    # 광추
    lcs = await _fetch_json(session, SRR_URLS["light_cones"])
    if lcs:
        _LC_KO.update(lcs)

    # 광추 중첩 효과
    lc_ranks = await _fetch_json(session, SRR_URLS["lc_ranks"])
    if lc_ranks:
        _LC_RANKS_KO.update(lc_ranks)

    # 유물 세트
    relics = await _fetch_json(session, SRR_URLS["relic_sets"])
    if relics:
        _RELIC_SETS_KO.update(relics)

    loaded = sum(1 for d in [_TAG_TO_KO, _SKILLS_KO, _LC_KO, _RELIC_SETS_KO] if d)
    return loaded > 0


# load_kr_names는 하위 호환용 별칭
load_kr_names = load_kr_data


SKILL_TYPE_KO = {
    'basic': '일반 공격', 'skill': '전투 스킬', 'ult': '필살기',
    'talent': '특성', 'technique': '비술',
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
    """Contentful rich text JSON → 평문 변환"""
    if not raw:
        return ""
    if isinstance(raw, str):
        # HTML 태그 제거
        text = re.sub(r'<[^>]+>', '', raw)
        return text.strip()

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
    """HTML 태그 제거"""
    return re.sub(r'<[^>]+>', '', text).strip()


def _get_ko_name(en_name: str, slug: str = "") -> str:
    """slug(tag) 기반으로 공식 한글 이름 조회. 없으면 영어 이름 반환."""
    if slug:
        ko = _TAG_TO_KO.get(slug.lower())
        if ko:
            return ko
    # slug이 없을 때 영어 이름을 소문자화해서 시도
    ko = _TAG_TO_KO.get(en_name.lower().replace(" ", "").replace(".", ""))
    return ko if ko else en_name


# ─── 캐릭터 ─────────────────────────────────────────

async def fetch_character_list(session: aiohttp.ClientSession) -> Dict[str, dict]:
    """캐릭터 목록. {한글이름: {slug, name_en, rarity, element, path}}"""
    data = await _fetch_page_data(session, "characters")
    if not data:
        return {}

    nodes = data.get("allCharacters", {}).get("nodes", [])
    result = {}
    for n in nodes:
        en_name = n.get("name", "")
        slug = n.get("slug", "")
        ko_name = _get_ko_name(en_name, slug)
        result[ko_name] = {
            "slug": n.get("slug", ""),
            "name_en": en_name,
            "rarity": int(n.get("rarity", 4)),
            "element": n.get("element", ""),
            "element_ko": ELEMENT_KO.get(n.get("element", ""), n.get("element", "")),
            "path": n.get("path", ""),
            "path_ko": PATH_KO.get(n.get("path", ""), n.get("path", "")),
            "createdAt": n.get("createdAt", ""),
        }
    return result


async def fetch_character_detail(session: aiohttp.ClientSession, slug: str) -> Optional[dict]:
    """캐릭터 상세 정보"""
    data = await _fetch_page_data(session, f"characters/{slug}")
    if not data:
        return None

    nodes = data.get("currentUnit", {}).get("nodes", [])
    if not nodes:
        return None

    u = nodes[0]
    en_name = u.get("name", slug)
    ko_name = _get_ko_name(en_name, slug)

    # ── StarRailRes에서 한글 스킬 데이터 가져오기 ──
    char_id = _CHAR_ID_BY_TAG.get(slug.lower(), "")
    # 캐릭터의 스킬 ID 목록 (characters.json에 있음)
    char_info_srr = None
    if char_id:
        chars_data = await _fetch_json(session, SRR_URLS["characters"])
        if chars_data:
            char_info_srr = chars_data.get(char_id, {})

    # 스킬 (한글 우선)
    skills = []
    skill_ids = char_info_srr.get("skills", []) if char_info_srr else []
    _type_map = {'Normal': 'basic', 'BPSkill': 'skill', 'Ultra': 'ult',
                 'Talent': 'talent', 'Maze': 'technique', 'MazeNormal': 'technique'}
    for sid in skill_ids:
        sid_str = str(sid)
        sk_data = _SKILLS_KO.get(sid_str)
        if not sk_data:
            continue
        sk_type = _type_map.get(sk_data.get("type", ""), "")
        if not sk_type:
            continue
        # 중복 타입 방지 (같은 타입 스킬이 여러 개일 수 있음 - 변신 등)
        if any(s["type"] == sk_type for s in skills):
            continue
        # 설명의 #N[i] 플레이스홀더를 Lv10 수치로 치환
        desc = sk_data.get("desc", "")
        params = sk_data.get("params", [])
        if params:
            # Lv10 또는 마지막 레벨 파라미터 사용
            lv_params = params[min(9, len(params)-1)] if params else []
            for i, val in enumerate(lv_params):
                placeholder = f"#{i+1}[i]"
                if placeholder in desc:
                    if isinstance(val, float) and val < 1:
                        desc = desc.replace(placeholder, f"{val*100:.0f}")
                    else:
                        desc = desc.replace(placeholder, str(int(val) if isinstance(val, float) and val == int(val) else val))
        skills.append({
            "type": sk_type,
            "type_ko": sk_data.get("type_text", SKILL_TYPE_KO.get(sk_type, sk_type)),
            "name": sk_data.get("name", ""),
            "desc": desc,
            "energy": sk_data.get("energy_gen", "") or u.get("skillsNew", {}).get(sk_type, {}).get("energy_gen", ""),
        })

    # Prydwen 폴백 (StarRailRes 데이터 없을 때)
    if not skills:
        skills_raw = u.get("skillsNew", {})
        if isinstance(skills_raw, dict):
            for key in ['basic', 'skill', 'ult', 'talent', 'technique']:
                sk = skills_raw.get(key)
                if sk and isinstance(sk, dict):
                    skills.append({
                        "type": key,
                        "type_ko": SKILL_TYPE_KO.get(key, key),
                        "name": "",
                        "desc": "",
                        "energy": sk.get("energy_gen", ""),
                    })

    # 에이도론 (한글 우선)
    eidolons = []
    rank_ids = char_info_srr.get("ranks", []) if char_info_srr else []
    for rid in rank_ids:
        rid_str = str(rid)
        r_data = _RANKS_KO.get(rid_str, {})
        if r_data:
            eidolons.append({"name": r_data.get("name", ""), "description": r_data.get("desc", "")})
    # Prydwen 폴백
    if not eidolons:
        eid_list = u.get("eidolon", [])
        if eid_list:
            e = eid_list[0]
            for i in range(1, 7):
                name = e.get(f"upgrade{i}Name", "")
                desc_raw = e.get(f"upgrade{i}Desc", "")
                desc = _contentful_to_text(desc_raw) if isinstance(desc_raw, dict) else _clean_html(str(desc_raw))
                eidolons.append({"name": name, "description": desc})

    # 트레이스 (패시브) — Prydwen 데이터 사용 (한글 소스에 세부 매핑 어려움)
    traces = []
    for t in u.get("traces", []):
        traces.append({
            "req": t.get("req", ""),
            "desc": _clean_html(t.get("desc", "")),
        })

    # 스탯
    stats = u.get("stats", {})

    # 육성재료
    mats = u.get("ascensionMaterials", {})
    mat_names = [v for k, v in sorted(mats.items()) if v]

    # 설명
    desc = _contentful_to_text(u.get("description", {}))

    return {
        "name": ko_name,
        "name_en": en_name,
        "slug": slug,
        "rarity": int(u.get("rarity", 4)),
        "element": u.get("element", ""),
        "element_ko": ELEMENT_KO.get(u.get("element", ""), ""),
        "path": u.get("path", ""),
        "path_ko": PATH_KO.get(u.get("path", ""), ""),
        "affiliation": u.get("affiliation", ""),
        "description": desc,
        "skills": skills,
        "eidolons": eidolons,
        "traces": traces,
        "stats": stats,
        "ascension_mats": mat_names,
        "energy_ult": u.get("energyUltimate", ""),
        "url": f"https://www.prydwen.gg/star-rail/characters/{slug}",
        "icon_url": "",
    }


# ─── 광추 ─────────────────────────────────────────

async def fetch_lightcone_list(session: aiohttp.ClientSession) -> Dict[str, dict]:
    """광추 목록. {한글이름: {slug, rarity, path}}"""
    data = await _fetch_page_data(session, "light-cones")
    if not data:
        return {}

    nodes = data.get("allCharacters", {}).get("nodes", [])
    result = {}
    for n in nodes:
        en_name = n.get("name", "")
        slug = n.get("slug", "")
        # StarRailRes에서 한글 이름 찾기
        ko_name = en_name
        for lc_id, lc_info in _LC_KO.items():
            if lc_info.get("name", "") and en_name.lower().replace(" ", "") == lc_info.get("name", "").lower().replace(" ", ""):
                ko_name = lc_info["name"]
                break
            # slug으로도 매칭 시도 (광추는 tag 없으므로 이름 기반)
        result[ko_name] = {
            "slug": slug,
            "name_en": en_name,
            "rarity": int(n.get("rarity", 4)),
            "createdAt": n.get("createdAt", ""),
        }
    return result


async def fetch_lightcone_detail(session: aiohttp.ClientSession, slug: str) -> Optional[dict]:
    """광추 상세 (한글 우선)"""
    data = await _fetch_page_data(session, f"light-cones/{slug}")
    if not data:
        return None

    nodes = data.get("currentUnit", {}).get("nodes", [])
    if not nodes:
        return None

    lc = nodes[0]
    en_name = lc.get("name", slug)

    # StarRailRes에서 한글 데이터 찾기
    ko_name = en_name
    ko_desc = ""
    ko_si = ""
    for lc_id, lc_info in _LC_KO.items():
        # 이름이 아닌 ID로 매칭해야 하므로 lc_ranks에서 중첩 효과 찾기
        if lc_info.get("name", "") and en_name.lower().replace(" ", "").replace("'", "") in lc_info.get("name", "").lower().replace(" ", "").replace("'", "") or lc_info.get("name", "").lower().replace(" ", "") in en_name.lower().replace(" ", ""):
            ko_name = lc_info["name"]
            ko_desc = lc_info.get("desc", "")
            # 중첩 효과
            rank_data = _LC_RANKS_KO.get(lc_id, {})
            if rank_data:
                ko_si = rank_data.get("skill", "")
            break

    # Prydwen 폴백
    si_raw = lc.get("superimpose", "")
    si_text = ko_si or (_contentful_to_text(si_raw) if isinstance(si_raw, dict) else _clean_html(str(si_raw or "")))

    return {
        "name": ko_name,
        "name_en": en_name,
        "slug": slug,
        "rarity": int(lc.get("rarity", 4)),
        "path": lc.get("path", ""),
        "path_ko": PATH_KO.get(lc.get("path", ""), ""),
        "description": ko_desc,
        "superimpose": si_text,
        "url": f"https://www.prydwen.gg/star-rail/light-cones/{slug}",
    }


# ─── 유물 세트 ─────────────────────────────────────────

async def fetch_relic_list(session: aiohttp.ClientSession) -> Dict[str, dict]:
    """유물 세트 목록. {한글이름: {name, type, bonus2, bonus4}}"""
    data = await _fetch_page_data(session, "guides/relic-sets")
    if not data:
        return {}

    nodes = data.get("allCharacters", {}).get("nodes", [])
    result = {}
    for n in nodes:
        en_name = n.get("name", "")
        # StarRailRes에서 한글 유물 세트 찾기
        ko_name = en_name
        ko_b2 = ""
        ko_b4 = ""
        for sid, sinfo in _RELIC_SETS_KO.items():
            s_name = sinfo.get("name", "")
            if s_name and (en_name.lower().replace(" ", "") in s_name.lower().replace(" ", "") or s_name.lower().replace(" ", "") in en_name.lower().replace(" ", "")):
                ko_name = s_name
                descs = sinfo.get("desc", [])
                if len(descs) >= 1:
                    ko_b2 = descs[0]
                if len(descs) >= 2:
                    ko_b4 = descs[1]
                break

        b2 = ko_b2 or _contentful_to_text(n.get("bonus2", {}))
        b4 = ko_b4 or _contentful_to_text(n.get("bonus4", {}))
        result[ko_name] = {
            "name": ko_name,
            "name_en": en_name,
            "type": n.get("type", ""),
            "bonus2": b2,
            "bonus4": b4,
        }
    return result


# ─── 검색 유틸 ─────────────────────────────────────────

def search_items(query: str, item_dict: dict, limit: int = 10) -> list:
    """이름 검색 (부분 일치, 한/영 모두). 반환: [(이름, value), ...]"""
    query_lower = query.lower()

    # 정확 일치
    exact = [(name, val) for name, val in item_dict.items() if name.lower() == query_lower]
    if exact:
        return exact

    # 영어 이름도 검색 (캐릭터의 경우)
    for name, val in item_dict.items():
        if isinstance(val, dict) and val.get("name_en", "").lower() == query_lower:
            return [(name, val)]

    # 부분 일치 (한글 + 영어)
    partial = []
    for name, val in item_dict.items():
        if query_lower in name.lower():
            partial.append((name, val))
        elif isinstance(val, dict) and query_lower in val.get("name_en", "").lower():
            partial.append((name, val))
    return partial[:limit]
