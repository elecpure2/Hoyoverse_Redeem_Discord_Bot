"""
Honey Hunter World 스크래퍼
원신(Genshin Impact) 캐릭터, 무기, 성유물 데이터를 스크래핑합니다.
"""
import aiohttp
import re
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Tuple

BASE_URL = "https://gensh.honeyhunterworld.com"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

# 원소 영/한 매핑
ELEMENT_KO = {
    'Anemo': '바람', 'Pyro': '불', 'Hydro': '물', 'Electro': '번개',
    'Cryo': '얼음', 'Geo': '바위', 'Dendro': '풀', 'None': '무',
}

# 무기 타입 영/한 매핑
WEAPON_TYPE_KO = {
    'Sword': '한손검', 'Claymore': '양손검', 'Polearm': '장병기',
    'Bow': '활', 'Catalyst': '법구',
}

# 무기 부옵 영/한 매핑
SUBSTAT_KO = {
    'HP %': 'HP%', 'ATK %': '공격력%', 'DEF %': '방어력%',
    'Critical Rate %': '치명타 확률%', 'Critical DMG %': '치명타 피해%',
    'Energy Recharge %': '원소 충전 효율%', 'Elemental Mastery': '원소 마스터리',
    'Physical DMG Bonus %': '물리 피해 보너스%',
}

# 무기 목록 페이지 URL
WEAPON_LIST_URLS = {
    'Sword': '/fam_sword/',
    'Claymore': '/fam_claymore/',
    'Polearm': '/fam_polearm/',
    'Bow': '/fam_bow/',
    'Catalyst': '/fam_catalyst/',
}

# 테스트/체험 캐릭터 제외 패턴
_EXCLUDE_PATTERNS = ('kate_', 'qin_01', 'qin_04', 'ambor_008', 'playerboy_04', 'playergirl_04')


# ─── 유틸 ─────────────────────────────────────────────

async def _fetch_html(session: aiohttp.ClientSession, path: str) -> Optional[str]:
    """URL에서 원본 HTML 텍스트 반환"""
    url = f"{BASE_URL}{path}" if path.startswith("/") else path
    if "?lang=" not in url:
        url += "?lang=KO" if "?" not in url else "&lang=KO"
    try:
        async with session.get(url, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=15)) as resp:
            if resp.status != 200:
                return None
            return await resp.text()
    except Exception:
        return None


async def _fetch_soup(session: aiohttp.ClientSession, path: str) -> Optional[BeautifulSoup]:
    """URL에서 HTML 파싱된 BeautifulSoup 반환"""
    html = await _fetch_html(session, path)
    if not html:
        return None
    return BeautifulSoup(html, "lxml")


def _decode_js(html: str) -> str:
    """JS 이스케이프 해제 (sortable_data의 HTML 문자열을 파싱용으로)"""
    decoded = html.replace('\\/', '/').replace('\\"', '"')
    # \\uXXXX 유니코드 이스케이프 해제 (한글 등)
    decoded = re.sub(r'\\u([0-9a-fA-F]{4})', lambda m: chr(int(m.group(1), 16)), decoded)
    return decoded


def _extract_name_slug_pairs(html: str, slug_pattern: str) -> Dict[str, str]:
    """이스케이프 해제된 HTML에서 <a href="/slug/?lang=KO">이름</a> 패턴 추출"""
    decoded = _decode_js(html)
    pairs = re.findall(rf'<a href="/({slug_pattern})/\?lang=KO">([^<]+)</a>', decoded)
    result = {}
    for slug, name in pairs:
        if name not in result:
            result[name] = slug
    return result


def _count_stars(row) -> int:
    """Rarity 행에서 별 이미지 수를 세서 성급 반환"""
    return len(row.select("img[src*='star']"))


def _clean_desc(text: str) -> str:
    """HH 내부 태그 정제: {LINK#...}, <color>, <a>태그 등 제거"""
    # {LINK#Sxxxxx} → 빈 문자열
    text = re.sub(r'\{LINK#[^}]*\}', '', text)
    # <color>...</color> → 내용만
    text = re.sub(r'</?color>', '', text)
    # 남은 HTML 태그 제거
    text = re.sub(r'<[^>]+>', '', text)
    # 다중 공백 정리
    text = re.sub(r'\s{2,}', ' ', text).strip()
    return text


def _extract_materials_with_qty(cell) -> list:
    """재료 셀에서 (이름, 수량) 쌍 추출. img alt + 바로 뒤 <span>에서 수량."""
    results = []
    seen = set()
    for img in cell.select("img"):
        alt = img.get("alt", "").strip()
        if not alt or alt in seen:
            continue
        seen.add(alt)
        # 수량: img 다음 sibling span 또는 text
        qty = ""
        ns = img.next_sibling
        if ns and hasattr(ns, 'name') and ns.name == 'span':
            qty = ns.get_text(strip=True)
        elif ns and hasattr(ns, 'name') and ns.name == 'a':
            # a 안에 span이 있을 수 있음
            span = ns.find('span')
            if span:
                qty = span.get_text(strip=True)
        results.append((alt, qty))
    return results


def _parse_info_table(table) -> Tuple[dict, int]:
    """기본 정보 테이블 파싱. (info_dict, rarity) 반환."""
    info = {}
    rarity = 4
    for row in table.select("tr"):
        cells = row.select("td, th")
        cell_texts = [c.get_text(strip=True) for c in cells]
        if any("Rarity" in t for t in cell_texts):
            rarity = _count_stars(row)
            continue
        for t in cell_texts:
            if t and t not in ("", " "):
                val = cell_texts[-1] if cell_texts[-1] != t else ""
                if t != val:
                    info[t] = val
                break
    return info, rarity


# ─── 캐릭터 ─────────────────────────────────────────────

async def fetch_character_list(session: aiohttp.ClientSession) -> Dict[str, str]:
    """캐릭터 목록 반환: {이름: slug}"""
    html = await _fetch_html(session, "/fam_chars/")
    if not html:
        return {}
    
    raw = _extract_name_slug_pairs(html, r'[a-z_]+_\d+')
    
    result = {}
    seen_slugs = set()
    for name, slug in raw.items():
        if any(slug.startswith(p) for p in _EXCLUDE_PATTERNS):
            continue
        if '체험' in name or '테스트' in name:
            continue
        if slug in seen_slugs:
            continue
        seen_slugs.add(slug)
        result[name] = slug
    
    return result


async def fetch_character_detail(session: aiohttp.ClientSession, slug: str) -> Optional[dict]:
    """캐릭터 상세 정보 반환"""
    soup = await _fetch_soup(session, f"/{slug}/")
    if not soup:
        return None
    
    content = soup.select_one(".entry-content") or soup
    tables = content.select("table")
    if not tables:
        return None
    
    info, rarity = _parse_info_table(tables[0])
    element = info.get("Element", "None")
    
    # 스킬/패시브/별자리 링크 추출 (중복 제거)
    skills, passives, constellations = [], [], []
    seen_paths = set()
    for a in content.select("a"):
        href = a.get("href", "")
        name = a.get_text(strip=True)
        if not name or not href:
            continue
        path = href.split("?")[0].strip("/").split("/")[-1] if "/" in href else href.split("?")[0]
        if path in seen_paths:
            continue
        seen_paths.add(path)
        if path.startswith("s_"):
            skills.append({"name": name, "path": path})
        elif path.startswith("p_"):
            passives.append({"name": name, "path": path})
        elif re.match(r'^c_\d+$', path):
            constellations.append({"name": name, "path": path})
    
    # 육성재료 추출 (Total Materials 열에서 img alt + span 수량)
    ascension_mats = []
    talent_mats = []
    for table in tables:
        header = table.select("tr")[0] if table.select("tr") else None
        if not header:
            continue
        header_text = header.get_text(strip=True)
        if "Total Materials" not in header_text:
            continue
        
        header_cells = [c.get_text(strip=True) for c in header.select("td, th")]
        tm_idx = next((i for i, h in enumerate(header_cells) if h == "Total Materials"), None)
        if tm_idx is None:
            continue
        
        # Total Materials 열에서 이미지가 있는 마지막 행
        best = []
        for row in table.select("tr")[1:]:
            cells = row.select("td, th")
            if len(cells) > tm_idx:
                mat_cell = cells[tm_idx]
                pairs = _extract_materials_with_qty(mat_cell)
                if pairs:
                    best = pairs
        
        if best:
            if "Atk" in header_text or "HP" in header_text:
                ascension_mats = best
            else:
                talent_mats = best
    
    # 중복 제거: 두 테이블이 동일하면 하나로 통합
    if ascension_mats and talent_mats:
        asc_names = set(n for n, _ in ascension_mats)
        tal_names = set(n for n, _ in talent_mats)
        if asc_names == tal_names:
            talent_mats = []
    
    return {
        "name": info.get("Name", slug),
        "title": info.get("Title", ""),
        "rarity": rarity,
        "element": element,
        "element_ko": ELEMENT_KO.get(element, element),
        "weapon": info.get("Weapon", ""),
        "weapon_ko": WEAPON_TYPE_KO.get(info.get("Weapon", ""), info.get("Weapon", "")),
        "association": info.get("Association", ""),
        "description": info.get("Description", ""),
        "constellation": info.get("Constellation (Introduced)", info.get("Constellation (Discovered)", "")),
        "skills": skills,
        "passives": passives,
        "constellations": constellations[:6],
        "ascension_mats": ascension_mats,
        "talent_mats": talent_mats,
        "icon_url": f"{BASE_URL}/img/{slug}_icon.webp",
        "splash_url": f"{BASE_URL}/img/{slug}_gacha_splash.webp",
        "url": f"{BASE_URL}/{slug}/?lang=KO",
    }


async def fetch_skill_detail(session: aiohttp.ClientSession, skill_path: str) -> Optional[dict]:
    """스킬/패시브 상세 정보 (설명 + Lv10 수치표)"""
    soup = await _fetch_soup(session, f"/{skill_path}/")
    if not soup:
        return None
    
    content = soup.select_one(".entry-content") or soup
    tables = content.select("table")
    if not tables:
        return None
    
    desc = ""
    for row in tables[0].select("tr"):
        cells = row.select("td, th")
        cell_texts = [c.get_text(strip=True) for c in cells]
        if any("Description" in t for t in cell_texts):
            desc = _clean_desc(cells[-1].get_text(strip=True))
            break
    
    stats_lv10 = {}
    if len(tables) >= 2:
        header = tables[1].select("tr")[0]
        header_cells = [c.get_text(strip=True) for c in header.select("td, th")]
        lv10_idx = next((i for i, h in enumerate(header_cells) if h == "Lv10"), None)
        
        if lv10_idx:
            for row in tables[1].select("tr")[1:]:
                cells = row.select("td, th")
                cell_texts = [c.get_text(strip=True) for c in cells]
                if len(cell_texts) > lv10_idx and cell_texts[0]:
                    stats_lv10[cell_texts[0]] = cell_texts[lv10_idx]
    
    return {"description": desc, "stats_lv10": stats_lv10}


async def fetch_constellation_details(session: aiohttp.ClientSession, const_paths: list) -> list:
    """별자리 목록의 상세 설명을 한 번에 가져옴"""
    results = []
    for item in const_paths:
        soup = await _fetch_soup(session, f"/{item['path']}/")
        if not soup:
            results.append({"name": item["name"], "description": ""})
            continue
        
        content = soup.select_one(".entry-content") or soup
        tables = content.select("table")
        desc = ""
        if tables:
            for row in tables[0].select("tr"):
                cells = row.select("td, th")
                cell_texts = [c.get_text(strip=True) for c in cells]
                if any("Description" in t for t in cell_texts):
                    desc = _clean_desc(cells[-1].get_text(strip=True))
                    break
        results.append({"name": item["name"], "description": desc})
    return results


# ─── 무기 ─────────────────────────────────────────────

async def fetch_weapon_list(session: aiohttp.ClientSession) -> Dict[str, Tuple[str, str]]:
    """무기 목록 반환: {이름: (slug, 무기타입)}"""
    result = {}
    
    for wtype, path in WEAPON_LIST_URLS.items():
        html = await _fetch_html(session, path)
        if not html:
            continue
        
        pairs = _extract_name_slug_pairs(html, r'i_n\d+')
        for name, slug in pairs.items():
            if name != "n/a" and name not in result:
                result[name] = (slug, wtype)
    
    return result


async def fetch_weapon_detail(session: aiohttp.ClientSession, slug: str) -> Optional[dict]:
    """무기 상세 정보 반환"""
    soup = await _fetch_soup(session, f"/{slug}/")
    if not soup:
        return None
    
    content = soup.select_one(".entry-content") or soup
    tables = content.select("table")
    if not tables:
        return None
    
    info, rarity = _parse_info_table(tables[0])
    
    weapon_type = ""
    family = info.get("Family", "")
    for wt in WEAPON_TYPE_KO:
        if wt in family:
            weapon_type = wt
            break
    
    substat_raw = info.get("Substat Type", "")
    substat_ko = SUBSTAT_KO.get(substat_raw, substat_raw)
    
    return {
        "name": info.get("Name", slug),
        "rarity": rarity,
        "weapon_type": weapon_type,
        "weapon_type_ko": WEAPON_TYPE_KO.get(weapon_type, weapon_type),
        "base_attack": info.get("Base Attack", ""),
        "substat_type": substat_ko,
        "base_substat": info.get("Base Substat", ""),
        "affix_name": info.get("Weapon Affix", ""),
        "affix_desc": _clean_desc(info.get("Affix Description", "")),
        "description": info.get("Description", ""),
        "icon_url": f"{BASE_URL}/img/{slug}_gacha_icon_w145.webp",
        "url": f"{BASE_URL}/{slug}/?lang=KO",
    }


# ─── 성유물 ─────────────────────────────────────────────

async def fetch_artifact_list(session: aiohttp.ClientSession) -> Dict[str, str]:
    """성유물 세트 목록 반환: {이름: slug}"""
    html = await _fetch_html(session, "/fam_art_set/")
    if not html:
        return {}
    return _extract_name_slug_pairs(html, r'i_n4\d+')


async def fetch_artifact_detail(session: aiohttp.ClientSession, slug: str) -> Optional[dict]:
    """성유물 세트 상세 정보 반환"""
    soup = await _fetch_soup(session, f"/{slug}/")
    if not soup:
        return None
    
    content = soup.select_one(".entry-content") or soup
    tables = content.select("table")
    if not tables:
        return None
    
    info, rarity = _parse_info_table(tables[0])
    
    # 세트효과가 info에 없으면 테이블 전체에서 찾기
    two_piece = info.get("2-Piece Set", "")
    four_piece = info.get("4-Piece Set", "")
    
    if not two_piece:
        for table in tables:
            for row in table.select("tr"):
                cells = row.select("td, th")
                texts = [c.get_text(strip=True) for c in cells]
                for i, t in enumerate(texts):
                    if "2-Piece" in t and i + 1 < len(texts):
                        two_piece = texts[i + 1] if texts[i + 1] != t else ""
                    elif "4-Piece" in t and i + 1 < len(texts):
                        four_piece = texts[i + 1] if texts[i + 1] != t else ""
    
    return {
        "name": info.get("Name", slug),
        "rarity": rarity,
        "two_piece": two_piece,
        "four_piece": four_piece,
        "description": info.get("Description", ""),
        "icon_url": f"{BASE_URL}/img/{slug}_35.webp",
        "url": f"{BASE_URL}/{slug}/?lang=KO",
    }


# ─── 신규 콘텐츠 ─────────────────────────────────────────

async def fetch_latest_version(session: aiohttp.ClientSession) -> Optional[str]:
    """메인 페이지에서 최신 버전 번호 추출 (예: '6-4')"""
    html = await _fetch_html(session, "/")
    if not html:
        return None
    m = re.search(r'/new-in-(\d+-\d+)/', html)
    return m.group(1) if m else None


async def fetch_new_content(session: aiohttp.ClientSession, version: str = None) -> Optional[dict]:
    """신규 콘텐츠 (캐릭터/무기) 목록 반환"""
    if not version:
        version = await fetch_latest_version(session)
    if not version:
        return None
    
    soup = await _fetch_soup(session, f"/new-in-{version}/")
    if not soup:
        return None
    
    content = soup.select_one(".entry-content") or soup
    result = {"version": version.replace("-", "."), "characters": [], "weapons": []}
    
    current_section = None
    for el in content.descendants:
        if hasattr(el, 'name') and el.name == 'h2':
            current_section = el.get_text(strip=True)
        if hasattr(el, 'name') and el.name == 'a' and current_section:
            href = el.get("href", "")
            name = el.get_text(strip=True)
            if not name or not href:
                continue
            slug = href.split("?")[0].strip("/").split("/")[-1]
            
            if current_section == "Character":
                if re.match(r'^[a-z_]+_\d+$', slug):
                    result["characters"].append({"name": name, "slug": slug})
            elif current_section == "Weapon":
                if slug.startswith("i_n"):
                    result["weapons"].append({"name": name, "slug": slug})
    
    return result


# ─── 검색 유틸 ─────────────────────────────────────────

def search_items(query: str, item_dict: dict, limit: int = 10) -> list:
    """이름 검색 (부분 일치). 반환: [(이름, value), ...]"""
    query_lower = query.lower()
    exact = [(name, val) for name, val in item_dict.items() if name.lower() == query_lower]
    if exact:
        return exact
    
    partial = [(name, val) for name, val in item_dict.items() if query_lower in name.lower()]
    return partial[:limit]
