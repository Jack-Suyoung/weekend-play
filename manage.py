"""설정 관리 인터랙티브 CLI.

장소, 키워드, API 키 등을 쉽게 추가/수정/삭제할 수 있습니다.
실행: python manage.py
"""

import sys

import yaml

CONFIG_PATH = "config.yaml"


def load_config() -> dict:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def save_config(config: dict):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
    print(f"\n설정이 {CONFIG_PATH}에 저장되었습니다.")


def show_places(config: dict):
    places = config.get("places", [])
    if not places:
        print("\n등록된 장소가 없습니다.")
        return
    print("\n=== 등록된 장소 목록 ===")
    for i, place in enumerate(places, 1):
        cat = place.get("category", "")
        keywords = ", ".join(place.get("keywords", []))
        url = place.get("event_url", "") or "(없음)"
        print(f"\n  [{i}] {place['name']}")
        print(f"      카테고리: {cat}")
        print(f"      추가 키워드: {keywords or '(없음)'}")
        print(f"      이벤트 URL: {url}")


def add_place(config: dict):
    print("\n=== 새 장소 추가 ===")
    name = input("장소 이름: ").strip()
    if not name:
        print("취소되었습니다.")
        return

    keywords_input = input("추가 검색 키워드 (쉼표로 구분, 엔터로 건너뛰기): ").strip()
    keywords = [k.strip() for k in keywords_input.split(",") if k.strip()] if keywords_input else []

    event_url = input("이벤트 페이지 URL (엔터로 건너뛰기): ").strip()

    print("카테고리 선택:")
    print("  1) shopping - 쇼핑/복합몰")
    print("  2) park - 공원/자연")
    print("  3) culture - 문화/레저")
    cat_choice = input("선택 (1/2/3): ").strip()
    category_map = {"1": "shopping", "2": "park", "3": "culture"}
    category = category_map.get(cat_choice, "culture")

    place = {
        "name": name,
        "keywords": keywords,
        "event_url": event_url,
        "category": category,
    }

    config.setdefault("places", []).append(place)
    save_config(config)
    print(f"'{name}'이(가) 추가되었습니다.")


def edit_place(config: dict):
    places = config.get("places", [])
    if not places:
        print("\n등록된 장소가 없습니다.")
        return

    show_places(config)
    try:
        idx = int(input("\n수정할 장소 번호: ")) - 1
        if idx < 0 or idx >= len(places):
            print("잘못된 번호입니다.")
            return
    except ValueError:
        print("취소되었습니다.")
        return

    place = places[idx]
    print(f"\n'{place['name']}' 수정 (엔터를 누르면 기존 값 유지)")

    name = input(f"  이름 [{place['name']}]: ").strip()
    if name:
        place["name"] = name

    keywords_str = ", ".join(place.get("keywords", []))
    keywords_input = input(f"  추가 키워드 [{keywords_str}]: ").strip()
    if keywords_input:
        place["keywords"] = [k.strip() for k in keywords_input.split(",") if k.strip()]

    url = input(f"  이벤트 URL [{place.get('event_url', '')}]: ").strip()
    if url:
        place["event_url"] = url

    print("  카테고리:")
    print("    1) shopping  2) park  3) culture")
    cat_input = input(f"  선택 [{place.get('category', '')}]: ").strip()
    if cat_input in ("1", "2", "3"):
        category_map = {"1": "shopping", "2": "park", "3": "culture"}
        place["category"] = category_map[cat_input]

    save_config(config)
    print("수정되었습니다.")


def delete_place(config: dict):
    places = config.get("places", [])
    if not places:
        print("\n등록된 장소가 없습니다.")
        return

    show_places(config)
    try:
        idx = int(input("\n삭제할 장소 번호: ")) - 1
        if idx < 0 or idx >= len(places):
            print("잘못된 번호입니다.")
            return
    except ValueError:
        print("취소되었습니다.")
        return

    place = places[idx]
    confirm = input(f"'{place['name']}'을(를) 삭제하시겠습니까? (y/n): ").strip().lower()
    if confirm == "y":
        places.pop(idx)
        save_config(config)
        print("삭제되었습니다.")
    else:
        print("취소되었습니다.")


def edit_search_settings(config: dict):
    search = config.setdefault("search", {})

    print("\n=== 검색 설정 ===")
    print(f"  현재 검색 결과 수: {search.get('display_count', 10)}")
    print(f"  현재 날짜 필터: 최근 {search.get('days_filter', 14)}일")
    print(f"  현재 키워드 접미사: {', '.join(search.get('keyword_suffixes', []))}")

    count = input(f"\n검색 결과 수 [{search.get('display_count', 10)}]: ").strip()
    if count:
        search["display_count"] = int(count)

    days = input(f"날짜 필터 (일) [{search.get('days_filter', 14)}]: ").strip()
    if days:
        search["days_filter"] = int(days)

    suffixes = input(
        f"키워드 접미사 (쉼표 구분) [{', '.join(search.get('keyword_suffixes', []))}]: "
    ).strip()
    if suffixes:
        search["keyword_suffixes"] = [s.strip() for s in suffixes.split(",") if s.strip()]

    save_config(config)


def edit_api_keys(config: dict):
    api = config.setdefault("naver_api", {})
    print("\n=== Naver API 키 설정 ===")
    print("https://developers.naver.com/ 에서 발급받으세요.")

    current_id = api.get("client_id", "")
    masked_id = f"{current_id[:4]}****" if len(current_id) > 4 else "(미설정)"
    client_id = input(f"  Client ID [{masked_id}]: ").strip()
    if client_id:
        api["client_id"] = client_id

    current_secret = api.get("client_secret", "")
    masked_secret = f"{current_secret[:4]}****" if len(current_secret) > 4 else "(미설정)"
    client_secret = input(f"  Client Secret [{masked_secret}]: ").strip()
    if client_secret:
        api["client_secret"] = client_secret

    save_config(config)


def main():
    config = load_config()

    while True:
        print("\n" + "=" * 40)
        print("  Weekend Play - 설정 관리")
        print("=" * 40)
        print("  1) 장소 목록 보기")
        print("  2) 장소 추가")
        print("  3) 장소 수정")
        print("  4) 장소 삭제")
        print("  5) 검색 설정 변경")
        print("  6) API 키 설정")
        print("  q) 종료")
        print()

        choice = input("선택: ").strip().lower()

        if choice == "1":
            show_places(config)
        elif choice == "2":
            add_place(config)
            config = load_config()
        elif choice == "3":
            edit_place(config)
            config = load_config()
        elif choice == "4":
            delete_place(config)
            config = load_config()
        elif choice == "5":
            edit_search_settings(config)
            config = load_config()
        elif choice == "6":
            edit_api_keys(config)
            config = load_config()
        elif choice == "q":
            print("종료합니다.")
            break
        else:
            print("잘못된 입력입니다.")


if __name__ == "__main__":
    main()
