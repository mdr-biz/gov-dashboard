"""
서울경제진흥원(SBA) 사업공고 크롤러.
- URL: https://www.sba.seoul.kr/Pages/BusinessApply/OngoingList.aspx
- HTML 테이블 파싱. 상세 페이지는 JS 포스트백이라 목록 URL로 대체.
"""
from typing import List
from bs4 import BeautifulSoup
from .base import BaseSource, Notice


class SbaSource(BaseSource):
    source_id = "sba"
    source_name = "SBA 서울경제진흥원"
    tier = 4
    LIST_URL = "https://www.sba.seoul.kr/Pages/BusinessApply/OngoingList.aspx"

    def fetch(self) -> List[Notice]:
        notices: List[Notice] = []
        try:
            resp = self.session.get(self.LIST_URL, timeout=20)
            resp.encoding = "utf-8"
            soup = BeautifulSoup(resp.text, "html.parser")

            # 테이블에서 사업명 셀 찾기
            # SBA 페이지는 GridView1이라는 asp.net 테이블 사용
            tables = soup.find_all("table")
            for table in tables:
                rows = table.find_all("tr")
                for row in rows:
                    cells = row.find_all("td")
                    if len(cells) < 3:
                        continue

                    # 유형 (기업/개인 등) 확인 - 첫 셀
                    type_text = cells[0].get_text(strip=True)
                    if type_text not in ("기업", "개인", "기업+개인", "단체"):
                        continue

                    # 사업명 셀 (보통 2번째 셀)
                    title_cell = cells[1]
                    title_link = title_cell.find("a")
                    if title_link:
                        title = title_link.get_text(strip=True)
                    else:
                        title = title_cell.get_text(strip=True).split("\n")[0].strip()

                    if not title or len(title) < 5:
                        continue

                    # 접수 시작일/종료일 (마지막 셀 근처)
                    posted_date = ""
                    for cell in cells[2:]:
                        text = cell.get_text(strip=True)
                        # 날짜 패턴 (YYYY-MM-DD)
                        import re
                        m = re.search(r"(\d{4})-(\d{2})-(\d{2})", text)
                        if m:
                            posted_date = m.group(0)
                            break

                    notices.append(Notice(
                        source_id=self.source_id,
                        source_name=self.source_name,
                        tier=self.tier,
                        title=title,
                        url=self.LIST_URL,   # 상세 URL이 JS라 목록으로 대체
                        posted_date=posted_date,
                        category=f"모집공고 ({type_text})",
                    ))

            if not notices:
                print(f"[{self.source_id}] 공고 표를 찾지 못함")
        except Exception as e:
            print(f"[{self.source_id}] 수집 실패: {e}")
        return notices
