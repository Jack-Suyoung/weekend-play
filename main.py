"""Weekend Play - 주말 행사/팝업 자동 조회 파이프라인.

아키텍처:
  1. 복합 쇼핑몰 → 네이버 검색 API 수집 → Claude 분석으로 행사 추출
  2. 쇼핑몰 외 → 네이버 검색 API 수집 → Claude 분석으로 TOP 5 선별
  3. 최종 마크다운 리포트 생성

실행: python3 main.py
"""

import os
import sys

import yaml

from searcher import search_place, get_api_credentials, search_naver, filter_by_date, normalize_item
from analyzer import analyze_mall_events, analyze_local_events, generate_final_report
from report import save_report

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.yaml")
REPORTS_DIR = os.path.join(os.path.dirname(__file__), "reports")


def load_config() -> dict:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def search_local_events(config: dict) -> dict[str, list[dict]]:
    """강동/하남/구리 인근 지역 행사를 검색한다."""
    client_id, client_secret = get_api_credentials(config)
    search_config = config.get("search", {})
    display = search_config.get("display_count", 10)
    days = search_config.get("days_filter", 14)

    local_queries = [
        "서울 강동 축제 행사 2026년 4월",
        "하남 축제 행사 2026년 4월",
        "송파 석촌호수 벚꽃축제",
        "서울 강동 어린이 체험 행사",
        "광나루 한강공원 행사 축제",
        "일자산 행사 축제",
    ]

    results = {}
    for query in local_queries:
        all_items = []
        seen_links = set()
        for search_type in ["blog", "news"]:
            try:
                items = search_naver(query, client_id, client_secret, search_type, display)
                items = filter_by_date(items, days)
                for item in items:
                    normalized = normalize_item(item, search_type)
                    if normalized["link"] not in seen_links:
                        seen_links.add(normalized["link"])
                        all_items.append(normalized)
            except Exception:
                continue
        results[query] = all_items

    return results


def main():
    print("=" * 50)
    print("  Weekend Play - 주말 가족 행사/팝업 자동 조회")
    print("  (Claude 분석 기반)")
    print("=" * 50)
    print()

    # 1. 설정 로드
    config = load_config()
    places = config.get("places", [])
    if not places:
        print("등록된 장소가 없습니다. python manage.py로 장소를 추가하세요.")
        sys.exit(1)

    shopping_places = [p for p in places if p.get("category") == "shopping"]
    other_places = [p for p in places if p.get("category") != "shopping"]

    print(f"복합 쇼핑몰: {len(shopping_places)}곳")
    for p in shopping_places:
        print(f"  - {p['name']}")
    print(f"기타 장소: {len(other_places)}곳")
    for p in other_places:
        print(f"  - {p['name']}")
    print()

    # 2. 복합 쇼핑몰: 네이버 검색 → Claude 분석
    print("[1/3] 복합 쇼핑몰 행사 검색 중...")
    mall_sections = {}
    for place in shopping_places:
        name = place["name"]
        print(f"  검색 중: {name}...")
        try:
            raw_results = search_place(place, config)
            print(f"    -> {len(raw_results)}건 수집, Claude 분석 중...")
            analyzed = analyze_mall_events(name, raw_results)
            mall_sections[name] = analyzed
            print(f"    -> 분석 완료")
        except Exception as e:
            print(f"    -> 오류: {e}")
            mall_sections[name] = "_분석 중 오류가 발생했습니다._"
    print()

    # 3. 스타필드 하남 공식 사이트 정보 (WebFetch 가능한 유일한 곳)
    starfield_official = ""
    # 스타필드는 공식 사이트 fetch가 성공했으므로 하드코딩하지 않고
    # 검색 결과 기반 Claude 분석으로 대체

    # 4. 지역 행사 검색 → Claude 분석
    print("[2/3] 서울 강동 인근 행사/축제 검색 중...")
    try:
        local_raw = search_local_events(config)
        total_local = sum(len(v) for v in local_raw.values())
        print(f"  -> {total_local}건 수집, Claude 분석 중...")
        local_section = analyze_local_events(local_raw, max_count=5)
        print(f"  -> 분석 완료")
    except Exception as e:
        print(f"  -> 오류: {e}")
        local_section = "_분석 중 오류가 발생했습니다._"
    print()

    # 5. 리포트 생성
    print("[3/3] 리포트 생성 중...")
    report_content = generate_final_report(
        mall_sections, local_section, starfield_official
    )
    filepath = save_report(report_content, REPORTS_DIR)

    print(f"\n리포트가 생성되었습니다: {os.path.abspath(filepath)}")


if __name__ == "__main__":
    main()
