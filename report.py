"""마크다운 리포트 생성 및 HTML 변환 모듈."""

import os
from datetime import datetime

import markdown


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>주말 가족 나들이 리포트</title>
<style>
  :root {
    --bg: #fafaf9;
    --card: #ffffff;
    --text: #1c1917;
    --muted: #78716c;
    --accent: #f97316;
    --accent-light: #fff7ed;
    --border: #e7e5e4;
    --link: #ea580c;
  }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Apple SD Gothic Neo',
                 'Pretendard', 'Noto Sans KR', sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.7;
    padding: 0 0 4rem;
    -webkit-text-size-adjust: 100%;
  }
  .header {
    background: linear-gradient(135deg, #ea580c, #f97316);
    color: white;
    padding: 2rem 1.25rem 1.5rem;
    text-align: center;
  }
  .header h1 { font-size: 1.4rem; font-weight: 700; margin-bottom: .4rem; }
  .header p { font-size: .85rem; opacity: .9; }
  .container { max-width: 640px; margin: 0 auto; padding: 0 1rem; }
  h2 {
    font-size: 1.1rem;
    font-weight: 700;
    color: var(--accent);
    margin: 1.8rem 0 .8rem;
    padding-bottom: .4rem;
    border-bottom: 2px solid var(--accent);
    display: flex;
    align-items: center;
    gap: .4rem;
  }
  h3 {
    font-size: 1rem;
    font-weight: 700;
    margin: 1.2rem 0 .5rem;
    padding: .5rem .8rem;
    background: var(--accent-light);
    border-radius: 8px;
    border-left: 4px solid var(--accent);
  }
  ul, ol { padding-left: 0; list-style: none; }
  li {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: .8rem 1rem;
    margin-bottom: .6rem;
    box-shadow: 0 1px 3px rgba(0,0,0,.04);
  }
  li ul { margin-top: .4rem; }
  li li {
    background: transparent;
    border: none;
    box-shadow: none;
    padding: .15rem 0;
    margin: 0;
    font-size: .88rem;
    color: var(--muted);
  }
  strong { color: var(--text); }
  a { color: var(--link); text-decoration: none; font-weight: 500; }
  a:hover { text-decoration: underline; }
  blockquote {
    background: #fef3c7;
    border-left: 4px solid #f59e0b;
    padding: .7rem 1rem;
    margin: .8rem 0;
    border-radius: 0 8px 8px 0;
    font-size: .88rem;
    color: #92400e;
  }
  blockquote p { margin: .2rem 0; }
  p { margin: .5rem 0; }
  em { font-size: .85rem; color: var(--muted); }
  hr { border: none; border-top: 1px solid var(--border); margin: 1.5rem 0; }
  .footer {
    text-align: center;
    padding: 1.5rem;
    font-size: .8rem;
    color: var(--muted);
  }
  @media (prefers-color-scheme: dark) {
    :root {
      --bg: #1c1917;
      --card: #292524;
      --text: #fafaf9;
      --muted: #a8a29e;
      --border: #44403c;
      --accent-light: #431407;
      --link: #fb923c;
    }
    blockquote { background: #422006; color: #fde68a; }
  }
</style>
</head>
<body>
<div class="header">
  <h1>주말 가족 나들이 리포트</h1>
  <p>{{subtitle}}</p>
</div>
<div class="container">
{{content}}
</div>
<div class="footer">
  네이버 검색 API + Claude 분석으로 자동 생성
</div>
</body>
</html>"""


def save_report(content: str, output_dir: str = "reports") -> str:
    """리포트를 마크다운 + HTML 파일로 저장하고 파일 경로를 반환한다."""
    os.makedirs(output_dir, exist_ok=True)
    date_str = datetime.now().strftime("%Y-%m-%d")
    weekday_kr = ["월", "화", "수", "목", "금", "토", "일"][datetime.now().weekday()]

    # 마크다운 저장
    md_path = os.path.join(output_dir, f"{date_str}_weekend_report.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(content)

    # HTML 변환 및 저장
    md_extensions = ["extra", "nl2br", "sane_lists"]
    html_body = markdown.markdown(content, extensions=md_extensions)

    subtitle = f"{date_str} ({weekday_kr}) 생성"
    html_full = HTML_TEMPLATE.replace("{{content}}", html_body).replace(
        "{{subtitle}}", subtitle
    )

    # index.html로 저장 (GitHub Pages용)
    html_path = os.path.join(output_dir, "index.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_full)

    return md_path
