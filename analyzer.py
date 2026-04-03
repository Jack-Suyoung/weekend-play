"""Claude CLI를 활용한 지능형 콘텐츠 분석 모듈."""

import json
import subprocess


def call_claude(prompt: str, timeout: int = 120) -> str:
    """Claude CLI를 호출하여 응답을 반환한다."""
    result = subprocess.run(
        ["claude", "-p", prompt],
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Claude CLI 오류: {result.stderr}")
    return result.stdout.strip()


def analyze_mall_events(mall_name: str, raw_results: list[dict]) -> str:
    """쇼핑몰 검색 결과를 Claude로 분석하여 현재 진행 중인 행사를 추출한다."""
    if not raw_results:
        return f"## {mall_name}\n\n_조회된 행사 정보가 없습니다._\n"

    # 검색 결과를 텍스트로 변환
    entries = []
    for item in raw_results:
        entries.append(
            f"제목: {item['title']}\n"
            f"설명: {item.get('description', '')}\n"
            f"링크: {item.get('link', '')}\n"
            f"날짜: {item.get('date', '')}\n"
        )

    raw_text = "\n---\n".join(entries)

    prompt = f"""아래는 "{mall_name}"에 대한 네이버 블로그/뉴스 검색 결과입니다.

이 데이터를 분석해서 현재 {mall_name}에서 **실제로 진행 중이거나 곧 시작하는 행사, 팝업스토어, 이벤트, 축제**만 추출해주세요.

## 규칙:
1. **가족과 아이가 함께 즐길 수 있는 행사**를 우선순위로 해주세요
2. 주얼리, 향수 등 전시 관람형 브랜드 팝업은 제외해주세요
3. 같은 행사가 여러 기사/블로그에 나오면 하나로 합쳐주세요 (중복 제거)
4. 각 행사마다: 행사명, 기간, 간단한 설명(1줄), 참고 링크를 포함해주세요
5. **없는 정보를 절대 지어내지 마세요.** 검색 결과에 없는 행사를 추가하지 마세요.
6. 마크다운 리스트 형태로 출력해주세요
7. 행사가 없으면 "현재 확인된 가족 친화 행사가 없습니다."라고만 적어주세요

## 검색 결과:
{raw_text}

## 출력 형식 (마크다운):
- **행사명** (기간)
  - 설명
  - [참고 링크](URL)
"""

    return call_claude(prompt)


def analyze_local_events(raw_results: dict[str, list[dict]], max_count: int = 5) -> str:
    """쇼핑몰 외 지역 행사 검색 결과를 Claude로 분석하여 TOP N을 선별한다."""
    entries = []
    for place_name, items in raw_results.items():
        for item in items:
            entries.append(
                f"장소: {place_name}\n"
                f"제목: {item['title']}\n"
                f"설명: {item.get('description', '')}\n"
                f"링크: {item.get('link', '')}\n"
                f"날짜: {item.get('date', '')}\n"
            )

    if not entries:
        return "_조회된 지역 행사 정보가 없습니다._\n"

    raw_text = "\n---\n".join(entries)

    prompt = f"""아래는 서울 강동구, 하남, 구리 인근의 공원/문화시설 관련 네이버 블로그/뉴스 검색 결과입니다.

이 데이터에서 **현재 진행 중이거나 이번 주말에 열리는 행사, 축제, 페스티벌**을 선별해주세요.

## 규칙:
1. **서울 강동, 송파, 하남, 구리, 남양주 지역** 행사만 포함해주세요. 제주, 부산, 인천 월미도 등 타 지역은 제외.
2. **가족과 아이가 함께 즐길 수 있는 행사**를 우선순위로 해주세요
3. 같은 행사가 여러 번 나오면 하나로 합쳐주세요 (중복 제거)
4. **최대 {max_count}개**만 선별해주세요
5. 각 행사마다: 행사명, 장소, 기간, 간단한 설명(1줄), 참고 링크를 포함해주세요
6. **없는 정보를 절대 지어내지 마세요.**
7. 마크다운 리스트 형태로 출력해주세요
8. 해당하는 행사가 없으면 "현재 확인된 지역 행사가 없습니다."라고만 적어주세요

## 검색 결과:
{raw_text}

## 출력 형식 (마크다운):
- **행사명** — 장소 (기간)
  - 설명
  - [참고 링크](URL)
"""

    return call_claude(prompt)


def generate_final_report(
    mall_sections: dict[str, str],
    local_section: str,
    starfield_official: str,
) -> str:
    """Claude로 최종 리포트를 조합한다."""
    # 이 부분은 이미 구조화된 데이터이므로 직접 조합
    from datetime import datetime

    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    weekday_kr = ["월", "화", "수", "목", "금", "토", "일"][now.weekday()]

    lines = [
        "# 주말 가족 나들이 행사 리포트",
        "",
        f"> 생성일: {date_str} ({weekday_kr})",
        "> 우선순위: 복합 쇼핑몰 공식 행사 > 지역 축제/행사",
        "",
        "---",
        "",
        "## 복합 쇼핑몰 행사",
        "",
    ]

    for mall_name, section in mall_sections.items():
        lines.append(f"### {mall_name}")
        lines.append("")
        if starfield_official and "스타필드" in mall_name:
            lines.append("**[공식 사이트 확인]**")
            lines.append("")
            lines.append(starfield_official)
            lines.append("")
            lines.append("**[블로그/뉴스 기반 추가 정보]**")
            lines.append("")
        lines.append(section)
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## 서울 강동 인근 행사/축제 (TOP 5)")
    lines.append("")
    lines.append(local_section)
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("_이 리포트는 네이버 검색 API + Claude 분석으로 자동 생성되었습니다._")

    return "\n".join(lines)
