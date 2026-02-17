"""스타레일/젠존제 모듈 통합 테스트"""
import asyncio, aiohttp, sys
sys.path.insert(0, ".")
from utils.prydwen_hsr import fetch_character_list, fetch_character_detail, fetch_lightcone_list, fetch_relic_list, search_items as hsr_search
from utils.prydwen_zzz import fetch_agent_list, fetch_agent_detail, fetch_wengine_list, fetch_disk_list, search_items as zzz_search

async def main():
    async with aiohttp.ClientSession() as s:
        # ── HSR 테스트 ──
        print("=" * 50)
        print("스타레일 테스트")
        print("=" * 50)
        
        # 캐릭터 목록
        chars = await fetch_character_list(s)
        print(f"\n✅ 캐릭터 목록: {len(chars)}개")
        # 한국어 이름 확인
        sample = list(chars.items())[:5]
        for name, info in sample:
            print(f"  {name} ({info['name_en']}) — {info['rarity']}★ {info['element_ko']} {info['path_ko']}")
        
        # 검색 테스트
        results = hsr_search("카프카", chars)
        print(f"\n✅ '카프카' 검색: {len(results)}개 → {results[0][0] if results else '없음'}")
        
        results2 = hsr_search("kafka", chars)
        print(f"  'kafka' 검색: {len(results2)}개 → {results2[0][0] if results2 else '없음'}")
        
        results3 = hsr_search("반딧", chars)
        print(f"  '반딧' 검색: {len(results3)}개 → {results3[0][0] if results3 else '없음'}")
        
        # 캐릭터 상세
        detail = await fetch_character_detail(s, "kafka")
        if detail:
            print(f"\n✅ 카프카 상세:")
            print(f"  이름: {detail['name']} ({detail['name_en']})")
            print(f"  속성: {detail['element_ko']} | 운명: {detail['path_ko']}")
            print(f"  스킬: {len(detail['skills'])}개")
            for sk in detail['skills']:
                print(f"    - {sk['type_ko']} (에너지: {sk.get('energy', '?')})")
            print(f"  에이도론: {len(detail['eidolons'])}개")
            for i, e in enumerate(detail['eidolons'][:2]):
                print(f"    E{i+1}. {e['name']}: {e['description'][:60]}...")
            print(f"  트레이스: {len(detail['traces'])}개")
            print(f"  육성재료: {detail['ascension_mats']}")
        else:
            print("  ❌ 상세 실패")
        
        # 광추 목록
        lcs = await fetch_lightcone_list(s)
        print(f"\n✅ 광추 목록: {len(lcs)}개")
        sample_lc = list(lcs.items())[:3]
        for name, info in sample_lc:
            print(f"  {name} ({info['rarity']}★)")
        
        # 유물 세트
        relics = await fetch_relic_list(s)
        print(f"\n✅ 유물 세트: {len(relics)}개")
        sample_r = list(relics.items())[:2]
        for name, info in sample_r:
            print(f"  {name}: 2세트={info['bonus2'][:50]}...")
        
        # ── ZZZ 테스트 ──
        print("\n" + "=" * 50)
        print("젠존제 테스트")
        print("=" * 50)
        
        # 에이전트 목록
        agents = await fetch_agent_list(s)
        print(f"\n✅ 에이전트 목록: {len(agents)}개")
        sample_a = list(agents.items())[:5]
        for name, info in sample_a:
            print(f"  {name} ({info['name_en']}) — {info['rarity']} {info['element_ko']} {info['style_ko']}")
        
        # 검색 테스트
        results = zzz_search("미야비", agents)
        print(f"\n✅ '미야비' 검색: {len(results)}개 → {results[0][0] if results else '없음'}")
        
        results2 = zzz_search("ellen", agents)
        print(f"  'ellen' 검색: {len(results2)}개 → {results2[0][0] if results2 else '없음'}")
        
        # 에이전트 상세
        detail = await fetch_agent_detail(s, "miyabi")
        if detail:
            print(f"\n✅ 미야비 상세:")
            print(f"  이름: {detail['name']} ({detail['name_en']})")
            print(f"  속성: {detail['element_ko']} | 스타일: {detail['style_ko']}")
            print(f"  소속: {detail['faction']}")
            print(f"  마인드스케이프: {len(detail['talents'])}개")
            for i, t in enumerate(detail['talents'][:2]):
                print(f"    M{i+1}. {t['name']}: {t['description'][:60]}...")
        else:
            print("  ❌ 상세 실패")
        
        # W-엔진
        wes = await fetch_wengine_list(s)
        print(f"\n✅ W-엔진 목록: {len(wes)}개")
        sample_we = list(wes.items())[:3]
        for name, info in sample_we:
            print(f"  {name} ({info['rarity']}) — {info.get('type_ko', '?')}")
        
        # 디스크 세트
        disks = await fetch_disk_list(s)
        print(f"\n✅ 디스크 세트: {len(disks)}개")
        if disks:
            sample_d = list(disks.items())[:2]
            for name, info in sample_d:
                print(f"  {name}: 2세트={info.get('bonus2', '?')[:50]}")
        
        print("\n" + "=" * 50)
        print("테스트 완료!")

asyncio.run(main())
