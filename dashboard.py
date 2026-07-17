"""
수집한 공지를 검색·필터 가능한 HTML 대시보드로 렌더링.
결과는 docs/index.html 로 저장 → GitHub Pages가 이걸 웹페이지로 서빙.
"""
import json
from datetime import datetime, timedelta
from typing import List, Dict
from sources.base import Notice


TIER_COLORS = {
    1: "#1F3864",  # 네이비 (보조컬러)
    2: "#FF6A00",  # 오렌지 (메인컬러) - 로봇 핵심
    3: "#ED7D31",  # 오렌지 톤
    4: "#16a34a",
    5: "#7c3aed",
}
TIER_LABELS = {
    1: "통합 어그리게이터",
    2: "로봇 핵심",
    3: "식품·외식·프랜차이즈",
    4: "지자체",
    5: "해외진출·벤처",
}


def build_dashboard(notices: List[Notice], title: str, highlight_days: int) -> str:
    """공지 리스트를 받아 완성된 HTML 문자열 반환"""

    today = datetime.now()
    highlight_cutoff = (today - timedelta(days=highlight_days)).strftime("%Y-%m-%d")
    updated_str = today.strftime("%Y-%m-%d %H:%M")

    # 공지를 JSON으로 직렬화 (JS에서 검색/필터에 사용)
    notices_json = json.dumps(
        [n.to_dict() for n in notices],
        ensure_ascii=False,
    )

    # 사이트 필터 옵션 만들기
    source_names = sorted(set(n.source_name for n in notices))
    source_options = "".join(
        f'<option value="{name}">{name}</option>' for name in source_names
    )

    new_count = sum(1 for n in notices if n.posted_date >= highlight_cutoff)

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, 'Malgun Gothic', sans-serif;
    background: #f1f5f9; color: #1e293b; line-height: 1.5;
  }}
  .header {{
    background: #1F3864; color: white; padding: 24px 20px;
    position: sticky; top: 0; z-index: 100;
    box-shadow: 0 2px 8px rgba(0,0,0,0.15);
  }}
  .header-inner {{ max-width: 1000px; margin: 0 auto; }}
  .header h1 {{ font-size: 22px; font-weight: 700; display: flex; align-items: center; gap: 8px; }}
  .header .meta {{ font-size: 13px; opacity: 0.85; margin-top: 6px; }}
  .header .badge {{
    display: inline-block; background: #FF6A00; color: white;
    padding: 2px 10px; border-radius: 12px; font-size: 12px; font-weight: 600;
    margin-left: 8px;
  }}
  .controls {{
    max-width: 1000px; margin: 20px auto 0; padding: 0 20px;
    display: flex; gap: 10px; flex-wrap: wrap;
  }}
  .controls input, .controls select {{
    padding: 10px 14px; border: 1px solid #cbd5e1; border-radius: 8px;
    font-size: 14px; font-family: inherit;
  }}
  .controls input {{ flex: 1; min-width: 200px; }}
  .container {{ max-width: 1000px; margin: 16px auto; padding: 0 20px 60px; }}
  .notice-card {{
    background: white; border-radius: 10px; padding: 16px 18px; margin-bottom: 10px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08); transition: transform 0.1s, box-shadow 0.1s;
    border-left: 4px solid #cbd5e1;
  }}
  .notice-card:hover {{ transform: translateY(-1px); box-shadow: 0 4px 12px rgba(0,0,0,0.12); }}
  .notice-card.is-new {{ border-left-color: #FF6A00; background: #fff7ed; }}
  .notice-top {{ display: flex; align-items: center; gap: 8px; margin-bottom: 6px; flex-wrap: wrap; }}
  .tier-tag {{
    font-size: 11px; font-weight: 600; color: white;
    padding: 2px 8px; border-radius: 10px;
  }}
  .new-tag {{
    font-size: 11px; font-weight: 700; color: #FF6A00;
    background: #ffedd5; padding: 2px 8px; border-radius: 10px;
  }}
  .source-tag {{ font-size: 12px; color: #64748b; font-weight: 500; }}
  .notice-title {{ font-size: 15px; font-weight: 600; margin: 4px 0; }}
  .notice-title a {{ color: #1e293b; text-decoration: none; }}
  .notice-title a:hover {{ color: #1F3864; text-decoration: underline; }}
  .notice-meta {{ font-size: 12px; color: #94a3b8; }}
  .empty {{ text-align: center; padding: 60px 20px; color: #94a3b8; }}
  .count-info {{ max-width: 1000px; margin: 16px auto 0; padding: 0 20px;
                 font-size: 13px; color: #64748b; }}
  .footer {{ text-align: center; padding: 30px 20px; font-size: 12px; color: #94a3b8; }}
</style>
</head>
<body>
  <div class="header">
    <div class="header-inner">
      <h1>🤖 {title}</h1>
      <div class="meta">
        마지막 업데이트: {updated_str}
        <span class="badge">새 공지 {new_count}건</span>
      </div>
    </div>
  </div>

  <div class="controls">
    <input type="text" id="searchBox" placeholder="🔍 제목 검색 (예: 로봇, R&D, 수출...)" />
    <select id="tierFilter">
      <option value="">전체 분류</option>
      <option value="1">Tier 1 · 통합 어그리게이터</option>
      <option value="2">Tier 2 · 로봇 핵심</option>
      <option value="3">Tier 3 · 식품·외식·프랜차이즈</option>
      <option value="4">Tier 4 · 지자체</option>
      <option value="5">Tier 5 · 해외진출·벤처</option>
    </select>
    <select id="sourceFilter">
      <option value="">전체 사이트</option>
      {source_options}
    </select>
    <select id="newFilter">
      <option value="">전체 기간</option>
      <option value="new">최근 {highlight_days}일 새 공지만</option>
    </select>
  </div>

  <div class="count-info" id="countInfo"></div>
  <div class="container" id="noticeList"></div>

  <div class="footer">
    매일 오전 8시 자동 갱신 · 만다린로보틱스<br>
    설정 변경은 config.yaml 파일을 수정하세요.
  </div>

<script>
  const NOTICES = {notices_json};
  const HIGHLIGHT_CUTOFF = "{highlight_cutoff}";
  const TIER_COLORS = {json.dumps(TIER_COLORS)};
  const TIER_LABELS = {json.dumps(TIER_LABELS, ensure_ascii=False)};

  const searchBox = document.getElementById('searchBox');
  const tierFilter = document.getElementById('tierFilter');
  const sourceFilter = document.getElementById('sourceFilter');
  const newFilter = document.getElementById('newFilter');
  const noticeList = document.getElementById('noticeList');
  const countInfo = document.getElementById('countInfo');

  function render() {{
    const q = searchBox.value.trim().toLowerCase();
    const tier = tierFilter.value;
    const source = sourceFilter.value;
    const onlyNew = newFilter.value === 'new';

    let filtered = NOTICES.filter(n => {{
      if (q && !n.title.toLowerCase().includes(q)) return false;
      if (tier && String(n.tier) !== tier) return false;
      if (source && n.source_name !== source) return false;
      if (onlyNew && !(n.posted_date >= HIGHLIGHT_CUTOFF)) return false;
      return true;
    }});

    // 최신순 정렬
    filtered.sort((a, b) => (b.posted_date || '').localeCompare(a.posted_date || ''));

    countInfo.textContent = `총 ${{filtered.length}}건 표시 중`;

    if (filtered.length === 0) {{
      noticeList.innerHTML = '<div class="empty">조건에 맞는 공지가 없습니다.</div>';
      return;
    }}

    noticeList.innerHTML = filtered.map(n => {{
      const isNew = n.posted_date >= HIGHLIGHT_CUTOFF;
      const color = TIER_COLORS[n.tier] || '#64748b';
      const label = TIER_LABELS[n.tier] || '';
      return `
        <div class="notice-card ${{isNew ? 'is-new' : ''}}">
          <div class="notice-top">
            <span class="tier-tag" style="background:${{color}}">${{label}}</span>
            ${{isNew ? '<span class="new-tag">NEW</span>' : ''}}
            <span class="source-tag">📍 ${{n.source_name}}</span>
          </div>
          <div class="notice-title">
            <a href="${{n.url}}" target="_blank" rel="noopener">${{n.title}}</a>
          </div>
          <div class="notice-meta">${{n.category || ''}} ${{n.posted_date ? '· ' + n.posted_date : ''}}</div>
        </div>
      `;
    }}).join('');
  }}

  searchBox.addEventListener('input', render);
  tierFilter.addEventListener('change', render);
  sourceFilter.addEventListener('change', render);
  newFilter.addEventListener('change', render);
  render();
</script>
</body>
</html>
"""
    return html
