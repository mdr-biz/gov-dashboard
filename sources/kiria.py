"""
한국로봇산업진흥원(KIRIA) 크롤러.
- 사업공고: portalInfoBusinessList.do
- 공지사항: portalInfoNotiList.do
- 상세 URL은 JS 함수 fn_goBusinessDetail('IBUS_xxx') / fn_goNoticeDetail('NOTI_xxx')
  → JS 코드에서 ID를 추출해 실제 상세 URL을 구성
"""
import re
from typing import List
from bs4 import BeautifulSoup
from .base import BaseSource, Notice


class KiriaSource(BaseSource):
    source_id = "kiria"
    source_name = "한국로봇산업진흥원"
    tier = 2

    BOARDS = [
        {
            "category": "사업공고",
            "list_url": "https://www.kiria.org/portal/info/portalInfoBusinessList.do",
            "detail_pattern": "https://www.kiria.org/portal/info/portalInfoBusinessWrite.do?ibusCode={id}&mode=update",
            "js_func": "fn_goBusinessDetail",
        },
        {
            "category": "공지사항",
            "list_url": "https://www.kiria.org/portal/info/portalInfoNotiList.do",
            "detail_pattern": "https://www.kiria.org/portal/info/portalInfoNotiWrite.do?notiCode={id}&mode=update",
            "js_func": "fn_goNoticeDetail",
        },
        {
            "category": "입찰공고",
            "list_url": "https://www.kiria.org/portal/info/portalInfoTenderList.do",
            "detail_pattern": "https://www.kiria.org/portal/info/portalInfoTenderWrite.do?itendCode={id}&mode=update",
            "js_func": "fn_goTenderDetail",
        },
    ]

    def fetch(self) -> List[Notice]:
        notices: List[Notice] = []

        for board in self.BOARDS:
            try:
                resp = self.session.get(board["list_url"], timeout=15)
                resp.encoding = "utf-8"
                soup = BeautifulSoup(resp.text, "html.parser")

                # 게시판 표의 각 행
                rows = soup.select("table tbody tr")
                if not rows:
                    rows = soup.select("table tr")

                for row in rows:
                    # 제목이 있는 링크(a 태그) 찾기
                    link = row.find("a")
                    if not link:
                        continue

                    title = link.get_text(strip=True)
                    if not title or len(title) < 5:
                        continue

                    # 링크의 onclick 또는 href에서 ID 추출
                    onclick = link.get("onclick", "") or link.get("href", "")
                    # 예: fn_goBusinessDetail('IBUS_000000000001260')
                    m = re.search(rf"{board['js_func']}\('([^']+)'\)", onclick)

                    if m:
                        item_id = m.group(1)
                        url = board["detail_pattern"].format(id=item_id)
                    else:
                        url = board["list_url"]  # 목록 URL로 대체

                    # 날짜 찾기 (셀 중에서 YYYY-MM-DD 또는 YYYY/MM/DD 형식)
                    posted_date = ""
                    for cell in row.find_all("td"):
                        text = cell.get_text(strip=True)
                        m2 = re.search(r"(\d{4})[-./](\d{2})[-./](\d{2})", text)
                        if m2:
                            posted_date = f"{m2.group(1)}-{m2.group(2)}-{m2.group(3)}"
                            break

                    notices.append(Notice(
                        source_id=self.source_id,
                        source_name=self.source_name,
                        tier=self.tier,
                        title=title,
                        url=url,
                        posted_date=posted_date,
                        category=board["category"],
                    ))
            except Exception as e:
                print(f"[{self.source_id}] {board['category']} 수집 실패: {e}")

        return notices
