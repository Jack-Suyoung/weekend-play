"""주요 쇼핑몰 이벤트 페이지 직접 스크래핑 모듈.

각 스크래퍼는 실패 시 빈 리스트를 반환하여 전체 파이프라인을 중단하지 않는다.
"""

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}


def scrape_starfield_hanam() -> list[dict]:
    """스타필드 하남 이벤트 페이지를 스크래핑한다."""
    url = "https://www.starfield.co.kr/hanam/event/index.do"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        events = []
        # 이벤트 리스트 항목 탐색
        for item in soup.select(".event_list li, .evt_list li, .list_event li"):
            title_el = item.select_one("a, .tit, .title, strong")
            date_el = item.select_one(".date, .period, .evt_date, span")
            link_el = item.select_one("a[href]")

            title = title_el.get_text(strip=True) if title_el else ""
            date = date_el.get_text(strip=True) if date_el else ""
            link = ""
            if link_el and link_el.get("href"):
                href = link_el["href"]
                if href.startswith("http"):
                    link = href
                else:
                    link = f"https://www.starfield.co.kr{href}"

            if title:
                events.append({
                    "title": title,
                    "description": "",
                    "date": date,
                    "link": link,
                    "source": "스타필드 하남 공식",
                })
        return events
    except Exception:
        return []


def scrape_lotte_world_mall() -> list[dict]:
    """롯데월드몰 이벤트 페이지를 스크래핑한다."""
    url = "https://www.lwt.co.kr/culture/event/eventMain.do"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        events = []
        for item in soup.select(".event_list li, .evt_list li, .list_wrap li"):
            title_el = item.select_one("a, .tit, .title, strong, p")
            date_el = item.select_one(".date, .period, span")
            link_el = item.select_one("a[href]")

            title = title_el.get_text(strip=True) if title_el else ""
            date = date_el.get_text(strip=True) if date_el else ""
            link = ""
            if link_el and link_el.get("href"):
                href = link_el["href"]
                if href.startswith("http"):
                    link = href
                else:
                    link = f"https://www.lwt.co.kr{href}"

            if title:
                events.append({
                    "title": title,
                    "description": "",
                    "date": date,
                    "link": link,
                    "source": "롯데월드몰 공식",
                })
        return events
    except Exception:
        return []


# 스크래퍼 레지스트리: 장소 이름 키워드 -> 스크래퍼 함수
SCRAPER_REGISTRY = {
    "스타필드": scrape_starfield_hanam,
    "롯데월드몰": scrape_lotte_world_mall,
}


def scrape_place(place: dict) -> list[dict]:
    """장소에 맞는 스크래퍼를 찾아 실행한다."""
    name = place.get("name", "")
    results = []

    for keyword, scraper_fn in SCRAPER_REGISTRY.items():
        if keyword in name:
            scraped = scraper_fn()
            if scraped:
                results.extend(scraped)
            break

    return results


def scrape_all_places(config: dict) -> dict[str, list[dict]]:
    """모든 장소에 대해 스크래핑을 시도하고 결과를 반환한다."""
    results = {}
    places = config.get("places", [])

    for place in places:
        name = place["name"]
        if not place.get("event_url"):
            continue
        print(f"  스크래핑 중: {name}...")
        scraped = scrape_place(place)
        if scraped:
            results[name] = scraped
            print(f"    -> {len(scraped)}건 발견")
        else:
            print(f"    -> 스크래핑 결과 없음 (검색 결과로 대체)")

    return results
