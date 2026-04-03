"""Naver Search API를 활용한 장소별 행사/팝업 검색 모듈."""

import os
import re
from datetime import datetime, timedelta
from urllib.parse import quote

import requests


def get_api_credentials(config: dict) -> tuple[str, str]:
    """Naver API 인증 정보를 config 또는 환경변수에서 가져온다."""
    client_id = (
        os.environ.get("NAVER_CLIENT_ID")
        or config.get("naver_api", {}).get("client_id", "")
    )
    client_secret = (
        os.environ.get("NAVER_CLIENT_SECRET")
        or config.get("naver_api", {}).get("client_secret", "")
    )
    if not client_id or not client_secret:
        raise ValueError(
            "Naver API 인증 정보가 설정되지 않았습니다.\n"
            "config.yaml에 naver_api.client_id / client_secret을 설정하거나,\n"
            "환경변수 NAVER_CLIENT_ID / NAVER_CLIENT_SECRET을 설정해주세요.\n"
            "https://developers.naver.com/ 에서 애플리케이션을 등록하세요."
        )
    return client_id, client_secret


def strip_html(text: str) -> str:
    """HTML 태그를 제거한다."""
    return re.sub(r"<[^>]+>", "", text)


def search_naver(
    query: str,
    client_id: str,
    client_secret: str,
    search_type: str = "blog",
    display: int = 10,
) -> list[dict]:
    """네이버 검색 API를 호출하여 결과를 반환한다.

    Args:
        query: 검색 키워드
        search_type: "blog" 또는 "news"
        display: 결과 개수 (최대 100)
    """
    url = f"https://openapi.naver.com/v1/search/{search_type}.json"
    headers = {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret,
    }
    params = {
        "query": query,
        "display": display,
        "sort": "date",  # 최신순
    }

    resp = requests.get(url, headers=headers, params=params, timeout=10)
    resp.raise_for_status()
    return resp.json().get("items", [])


def filter_by_date(items: list[dict], days: int) -> list[dict]:
    """최근 N일 이내의 결과만 필터링한다."""
    cutoff = datetime.now() - timedelta(days=days)
    filtered = []
    for item in items:
        # 블로그: postdate (yyyymmdd), 뉴스: pubDate (RFC 2822)
        date_str = item.get("postdate") or item.get("pubDate", "")
        try:
            if len(date_str) == 8:  # yyyymmdd
                dt = datetime.strptime(date_str, "%Y%m%d")
            else:  # RFC 2822 format
                dt = datetime.strptime(date_str[:16].strip(), "%a, %d %b %Y")
        except (ValueError, IndexError):
            # 날짜 파싱 실패 시 포함
            filtered.append(item)
            continue
        if dt >= cutoff:
            filtered.append(item)
    return filtered


def normalize_item(item: dict, source: str) -> dict:
    """검색 결과를 통일된 형태로 정규화한다."""
    return {
        "title": strip_html(item.get("title", "")),
        "description": strip_html(item.get("description", "")),
        "link": item.get("link", "") or item.get("originallink", ""),
        "date": item.get("postdate") or item.get("pubDate", ""),
        "source": source,
    }


def search_place(place: dict, config: dict) -> list[dict]:
    """한 장소에 대해 모든 키워드 조합으로 검색하고 결과를 반환한다."""
    client_id, client_secret = get_api_credentials(config)
    search_config = config.get("search", {})
    display = search_config.get("display_count", 10)
    days = search_config.get("days_filter", 14)
    suffixes = search_config.get("keyword_suffixes", ["팝업", "행사", "이벤트"])

    # 검색할 키워드 목록 생성: 장소명 + 추가 키워드
    base_keywords = [place["name"]] + place.get("keywords", [])

    all_results = []
    seen_links = set()

    for keyword in base_keywords:
        for suffix in suffixes:
            query = f"{keyword} {suffix}"
            for search_type in ["blog", "news"]:
                try:
                    items = search_naver(
                        query, client_id, client_secret, search_type, display
                    )
                    items = filter_by_date(items, days)
                    for item in items:
                        normalized = normalize_item(item, search_type)
                        # 중복 제거 (같은 링크)
                        if normalized["link"] not in seen_links:
                            seen_links.add(normalized["link"])
                            all_results.append(normalized)
                except requests.RequestException:
                    continue

    return all_results


def search_all_places(config: dict) -> dict[str, list[dict]]:
    """모든 장소에 대해 검색을 수행하고 결과를 반환한다."""
    results = {}
    places = config.get("places", [])

    for place in places:
        name = place["name"]
        print(f"  검색 중: {name}...")
        place_results = search_place(place, config)
        results[name] = place_results
        print(f"    -> {len(place_results)}건 발견")

    return results
