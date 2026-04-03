"""검색 결과를 가족 친화 기준으로 점수화하고 필터링하는 모듈."""

import re
from collections import Counter


# 가족/아이 친화 키워드 → 가산점
FAMILY_BOOST_KEYWORDS = [
    ("아이", 3), ("키즈", 3), ("어린이", 3), ("가족", 3), ("패밀리", 3),
    ("체험", 3), ("놀이", 2), ("캐릭터", 2), ("티니핑", 3), ("포켓몬", 3),
    ("디즈니", 3), ("지브리", 3), ("보노보노", 3), ("산리오", 3),
    ("레고", 3), ("공룡", 3), ("동물", 2), ("반려", 2),
    ("축제", 2), ("페스타", 2), ("페스티벌", 2), ("마켓", 2), ("플리마켓", 2),
    ("푸드", 2), ("맛집", 1), ("먹거리", 2), ("셰프", 1),
    ("공연", 2), ("뮤지컬", 2), ("전시", 1), ("포토존", 1),
    ("워크숍", 2), ("만들기", 2), ("클래스", 1),
    ("벚꽃", 2), ("봄꽃", 2), ("꽃놀이", 2),
    ("수영장", 2), ("워터", 2), ("놀이터", 3),
    ("무료", 1), ("할인", 1), ("세일", 1),
]

# 제외 키워드 → 감점 또는 제외
EXCLUDE_KEYWORDS = [
    # 전시형/브랜드 팝업 (체험 없는 것)
    ("주얼리", -5), ("쥬얼리", -5), ("다이아몬드", -5), ("보석", -5),
    ("명품", -3), ("럭셔리", -3), ("하이엔드", -3),
    # 채용/부동산/금융
    ("채용", -10), ("구인", -10), ("입사", -10), ("면접", -10),
    ("부동산", -10), ("분양", -10), ("청약", -10), ("투자", -8),
    ("대출", -10), ("보험", -8), ("재테크", -8),
    # 성인/부적절
    ("성인", -10), ("19금", -10),
    # 법률/사건/사고
    ("소송", -10), ("재판", -10), ("폐업", -10), ("철거", -10),
    # 연예/논란/폭력 (무관한 뉴스)
    ("논란", -10), ("폭력", -10), ("폭행", -10), ("구설", -10),
    ("옹호", -10), ("폭로", -10), ("고소", -10), ("고발", -10),
    ("음주운전", -10), ("사망", -10), ("범죄", -10),
    ("버스킹", -3),  # 일회성 공연
    # 일회성/개인 일상 블로그
    ("일상", -3), ("먹방", -3), ("맛집추천", -2),
]

# 장소 카테고리별 우선순위 가산점
CATEGORY_PRIORITY = {
    "shopping": 5,   # 복합 쇼핑몰 최우선
    "culture": 2,
    "park": 1,
}

# 허용 지역 키워드 (이 중 하나라도 포함되어야 관련 지역으로 간주)
ALLOWED_LOCATIONS = [
    # 서울 강동/송파/광진 권역
    "강동", "고덕", "명일", "길동", "둔촌", "암사", "천호", "성내",
    "송파", "잠실", "석촌", "문정", "위례",
    "광진", "구의", "자양", "건대",
    # 경기 하남/구리/남양주
    "하남", "미사", "감일", "풍산",
    "구리", "인창", "수택", "교문",
    "남양주", "다산", "별내",
    # 대상 장소 이름 자체
    "스타필드", "롯데월드", "아이파크", "워커힐", "광나루", "일자산",
    "한강공원",
]

# 타 지역 키워드 (이것만 있고 허용 지역이 없으면 제외)
OTHER_LOCATIONS = [
    "제주", "부산", "대구", "대전", "광주", "울산", "세종",
    "방콕", "도쿄", "오사카", "싱가포르", "베트남", "태국",
    "강릉", "속초", "여수", "전주", "경주", "양산", "인천 월미",
    "성수동", "홍대", "이태원", "명동", "강남역", "신촌",
    "고양", "수원", "안성", "파주", "용인", "기흥",
]


def extract_keywords(text: str) -> set[str]:
    """텍스트에서 핵심 명사 키워드를 추출한다 (중복 행사 판별용)."""
    # 한글 2글자 이상 단어 추출
    words = re.findall(r"[가-힣]{2,}", text)
    # 불용어 제거
    stopwords = {
        "에서", "까지", "부터", "으로", "이상", "이하", "하는", "있는", "없는",
        "위한", "대한", "통해", "관련", "진행", "예정", "기간", "장소", "운영",
        "오전", "오후", "매일", "주말", "평일", "안내", "정보", "소식", "총정리",
        "후기", "추천", "가볼만한곳", "가기좋은", "블로그", "뉴스",
        # 뉴스 상투어
        "개최", "개막", "시동", "공개", "출시", "선보", "발표", "오픈",
        "최대", "상반기", "하반기", "올해", "지난해",
        "신세계", "그룹", "계열사", "관계자",
        # 장소명 (중복 판별 시 노이즈)
        "스타필드", "하남", "수원", "롯데", "월드몰", "현대", "아울렛",
        "구리", "잠실", "워커힐", "광나루", "한강공원", "일자산",
    }
    return {w for w in words if w not in stopwords and len(w) >= 2}


def is_same_event(item_a: dict, item_b: dict, threshold: float = 0.3) -> bool:
    """두 항목이 같은 행사/이벤트에 대한 것인지 판별한다."""
    text_a = f"{item_a.get('title', '')} {item_a.get('description', '')}"
    text_b = f"{item_b.get('title', '')} {item_b.get('description', '')}"

    kw_a = extract_keywords(text_a)
    kw_b = extract_keywords(text_b)

    if not kw_a or not kw_b:
        return False

    overlap = kw_a & kw_b
    smaller = min(len(kw_a), len(kw_b))

    if smaller == 0:
        return False

    similarity = len(overlap) / smaller
    return similarity >= threshold


def is_local_area(item: dict, place: dict) -> bool:
    """결과가 우리 동네(서울 강동/하남/구리 권역) 관련인지 확인한다."""
    text = f"{item.get('title', '')} {item.get('description', '')}"

    # 대상 장소 이름이 텍스트에 있으면 무조건 통과
    place_name = place.get("name", "")
    for keyword in place.get("keywords", []) + [place_name]:
        if keyword in text:
            return True

    # 허용 지역 키워드 체크
    has_local = any(loc in text for loc in ALLOWED_LOCATIONS)

    # 타 지역만 언급되고 우리 동네 언급이 없으면 제외
    has_other = any(loc in text for loc in OTHER_LOCATIONS)

    if has_local:
        return True
    if has_other and not has_local:
        return False

    # 어떤 지역도 언급 안 되면 통과 (일반적인 행사 정보일 수 있음)
    return True


def score_item(item: dict, place: dict) -> int:
    """검색 결과 항목에 점수를 매긴다."""
    text = f"{item.get('title', '')} {item.get('description', '')}".lower()
    score = 0

    # 카테고리 우선순위
    category = place.get("category", "")
    score += CATEGORY_PRIORITY.get(category, 0)

    # 가족 친화 키워드 가산
    for keyword, points in FAMILY_BOOST_KEYWORDS:
        if keyword in text:
            score += points

    # 제외 키워드 감점
    for keyword, points in EXCLUDE_KEYWORDS:
        if keyword in text:
            score += points  # points는 음수

    return score


def is_relevant(item: dict) -> bool:
    """명백히 관련 없는 결과를 걸러낸다."""
    text = f"{item.get('title', '')} {item.get('description', '')}".lower()

    # 강력 제외
    hard_exclude = [
        "채용", "구인", "부동산", "분양", "청약", "소송", "재판", "폐업",
        "논란", "폭력", "폭행", "폭로", "고소", "고발", "음주운전", "사망", "범죄",
    ]
    for keyword in hard_exclude:
        if keyword in text:
            return False

    return True


def deduplicate_events(items: list[dict]) -> list[dict]:
    """같은 행사에 대한 중복 기사/블로그를 제거한다.

    같은 행사에 대한 여러 기사 중 점수가 가장 높은 것만 남긴다.
    """
    if not items:
        return []

    # 그룹 할당: 각 아이템이 어떤 그룹에 속하는지
    groups: list[list[int]] = []  # 그룹별 아이템 인덱스

    for i, item in enumerate(items):
        merged = False
        for group in groups:
            # 그룹의 대표(첫 번째 항목)와 비교
            representative = items[group[0]]
            if is_same_event(item, representative):
                group.append(i)
                merged = True
                break
        if not merged:
            groups.append([i])

    # 각 그룹에서 최고 점수 항목만 선택
    result = []
    for group in groups:
        best_idx = max(group, key=lambda idx: items[idx].get("score", 0))
        result.append(items[best_idx])

    return result


def filter_and_rank(
    search_results: dict[str, list[dict]],
    scrape_results: dict[str, list[dict]],
    config: dict,
) -> list[dict]:
    """모든 결과를 통합하여 점수화, 필터링, 정렬한다.

    Returns:
        점수 기준 정렬된 리스트. 각 항목에 place_name, score 필드가 추가됨.
    """
    filter_config = config.get("filter", {})
    max_results = filter_config.get("max_results", 30)

    places_by_name = {p["name"]: p for p in config.get("places", [])}
    all_items = []

    # 스크래핑 결과 (공식 사이트 → 보너스 점수)
    for place_name, items in scrape_results.items():
        place = places_by_name.get(place_name, {})
        for item in items:
            if not is_relevant(item):
                continue
            if not is_local_area(item, place):
                continue
            score = score_item(item, place) + 3  # 공식 사이트 보너스
            all_items.append({**item, "place_name": place_name, "score": score})

    # 검색 결과
    for place_name, items in search_results.items():
        place = places_by_name.get(place_name, {})
        for item in items:
            if not is_relevant(item):
                continue
            if not is_local_area(item, place):
                continue
            score = score_item(item, place)
            if score < 0:
                continue
            all_items.append({**item, "place_name": place_name, "score": score})

    # 점수 내림차순 정렬
    all_items.sort(key=lambda x: x["score"], reverse=True)

    # 1단계: 제목 완전 중복 제거
    seen_titles = set()
    title_deduped = []
    for item in all_items:
        clean_title = re.sub(r"[^가-힣a-zA-Z0-9]", "", item["title"])
        if clean_title and clean_title not in seen_titles:
            seen_titles.add(clean_title)
            title_deduped.append(item)

    # 2단계: 같은 행사 중복 제거 (키워드 유사도 기반)
    deduped = deduplicate_events(title_deduped)

    return deduped[:max_results]
