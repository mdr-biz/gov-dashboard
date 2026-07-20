"""
서울경제진흥원(SBA) 사업공고 크롤러 - 개선판.
표 구조를 더 유연하게 파싱.
"""
import re
from typing import List
from bs4 import BeautifulSoup
from .base import BaseSource, Notice


class SbaSource(BaseSource):
    source_id = "sba"
    source_name = "SBA 서울경제진흥원"
    tier = 4
    LIST_URL = "https://www.sba.seoul.kr/Pages/BusinessApply/OngoingList.aspx"

    TYPE_KEYWORDS = ("기업", "개인", "단체", "예비창업")

    def fetch(self) -> List[Notice]:
        notices: List[Notice] = []
        try:
            resp = self.session.get(self.LIST_URL, timeout=20)
            resp.encoding = "utf-8"
            soup = BeautifulSoup(resp.text, "html.parser")

            found_any = False
            for table in soup.find_all("table"):
                rows = table.find_all("tr")
                for row in rows:
                    cells = row.find_all("td")
                    if len(cells) < 2:
                        continue

                    row_text = row.get_text(" ", strip=True)
                    if not any(k in row_text for k in self.TYPE_KEYWORDS):
                        continue

                    best_cell = None
                    best_len = 0
                    for cell in cells:
                        t = cell.get_text(strip=True)
                        if len(t) > best_len and len(t) < 200:
                            best_len = len(t)
                            best_cell = cell
                    if best_cell is None or best_len < 8:
                        continue

                    title = best_cell.get_text(" ", strip=True).split("\n")[0].strip()
                    if len(title) < 8:
                        continue

                    posted_date = ""
                    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", row_text)
                    if m:
                        posted_date = m.group(0)

                    category = "모집공고"
                    for k in self.TYPE_KEYWORDS:
                        if k in row_text:
                            category = f"모집공고 ({k})"
                            break

                    notices.append(Notice(
                        source_id=self.source_id,
                        source_name=self.source_name,
                        tier=self.tier,
                        title=title,
                        url=self.LIST_URL,
                        posted_date=posted_date,
                        category=category,
                    ))
                    found_any = True

            seen_titles = set()
            unique = []
            for n in notices:
                if n.title not in seen_titles:
                    seen_titles.add(n.title)
                    unique.append(n)
            notices = unique

            if not found_any:
                print(f"[{self.source_id}] 표에서 공고를 찾지 못함 - 사이트 구조 변경 가능성")
        except Exception as e:
            print(f"[{self.source_id}] 수집 실패: {e}")
        return notices
