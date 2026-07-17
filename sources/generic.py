"""
범용 게시판 크롤러.
대부분의 정부/기관 공지 게시판은 <table> 구조가 비슷해서
하나의 범용 크롤러로 여러 사이트를 처리할 수 있음.

각 사이트별 설정(URL, 도메인)은 GENERIC_BOARDS 에 정의.
"""
from typing import List
from bs4 import BeautifulSoup
from .base import BaseSource, Notice


# 사이트별 게시판 설정
# base_url: 상대링크를 절대링크로 만들 때 붙일 도메인
# boards: [(카테고리명, 게시판URL), ...]
GENERIC_BOARDS = {
    "kiria": {
        "name": "한국로봇산업진흥원",
        "tier": 2,
        "base_url": "https://www.kiria.org",
        "boards": [
            ("사업공고", "https://www.kiria.org/portal/board/list.do?menuNo=200070"),
            ("공지사항", "https://www.kiria.org/portal/board/list.do?menuNo=200069"),
        ],
    },
    "tipa": {
        "name": "TIPA 중소기업기술정보진흥원",
        "tier": 2,
        "base_url": "https://www.tipa.or.kr",
        "boards": [
            ("사업공고", "https://www.tipa.or.kr/tipa/notice/list.do"),
        ],
    },
    "foodpolis": {
        "name": "한국식품산업클러스터진흥원",
        "tier": 3,
        "base_url": "https://www.foodpolis.kr",
        "boards": [
            ("공지사항", "https://www.foodpolis.kr/servlet/kfc/bbs/BbsListView"),
        ],
    },
    "ikfa": {
        "name": "한국프랜차이즈산업협회",
        "tier": 3,
        "base_url": "https://www.ikfa.or.kr",
        "boards": [
            ("공지사항", "https://www.ikfa.or.kr/notice"),
        ],
    },
    "foodservice": {
        "name": "한국외식업중앙회",
        "tier": 3,
        "base_url": "https://www.foodservice.or.kr",
        "boards": [
            ("공지사항", "https://www.foodservice.or.kr/main/board/index.php?bbs_code=notice"),
        ],
    },
    "sba": {
        "name": "SBA 서울경제진흥원",
        "tier": 4,
        "base_url": "https://www.sba.seoul.kr",
        "boards": [
            ("모집공고", "https://www.sba.seoul.kr/kr/sbcu01s1"),
        ],
    },
    "gbsa": {
        "name": "경기도경제과학진흥원",
        "tier": 4,
        "base_url": "https://www.gbsa.or.kr",
        "boards": [
            ("사업공고", "https://www.gbsa.or.kr/user/board/List.do"),
        ],
    },
    "gepa": {
        "name": "경상북도경제진흥원",
        "tier": 4,
        "base_url": "https://www.gepa.kr",
        "boards": [
            ("사업공고", "https://www.gepa.kr/board/list.do"),
        ],
    },
    "venture": {
        "name": "벤처기업협회",
        "tier": 5,
        "base_url": "https://www.venture.or.kr",
        "boards": [
            ("사업공고", "https://www.venture.or.kr/biz/bizList.do"),
        ],
    },
    "kiat": {
        "name": "KIAT 한국산업기술진흥원",
        "tier": 5,
        "base_url": "https://www.kiat.or.kr",
        "boards": [
            ("사업공고", "https://www.kiat.or.kr/front/board/boardContentsListPage.do"),
        ],
    },
    "kar": {
        "name": "한국AI·로봇산업협회",
        "tier": 2,
        "base_url": "https://www.korearobot.or.kr",
        "boards": [
            ("공지사항", "https://www.korearobot.or.kr/notice"),
        ],
    },
}


class GenericBoardSource(BaseSource):
    """설정 기반 범용 게시판 크롤러"""

    def __init__(self, source_id: str):
        super().__init__()
        cfg = GENERIC_BOARDS[source_id]
        self.source_id = source_id
        self.source_name = cfg["name"]
        self.tier = cfg["tier"]
        self.base_url = cfg["base_url"]
        self.boards = cfg["boards"]

    def fetch(self) -> List[Notice]:
        notices: List[Notice] = []

        for category, board_url in self.boards:
            try:
                resp = self.session.get(board_url, timeout=15)
                resp.encoding = resp.apparent_encoding or "utf-8"
                soup = BeautifulSoup(resp.text, "html.parser")

                # 게시판 표의 각 행 탐색
                rows = soup.select("table tbody tr") or soup.select("table tr")

                for row in rows:
                    link = row.find("a")
                    if not link:
                        continue

                    title = link.get_text(strip=True)
                    if not title or len(title) < 3:
                        continue

                    href = link.get("href", "")
                    if href.startswith("/"):
                        url = self.base_url + href
                    elif href.startswith("http"):
                        url = href
                    else:
                        url = board_url

                    # 날짜 추출
                    posted_date = ""
                    cells = row.find_all("td")
                    for cell in reversed(cells):
                        text = cell.get_text(strip=True)
                        if len(text) >= 8 and sum(c.isdigit() for c in text) >= 6 \
                           and any(sep in text for sep in "-./"):
                            posted_date = text.replace(".", "-").replace("/", "-").strip("-")
                            break

                    notices.append(Notice(
                        source_id=self.source_id,
                        source_name=self.source_name,
                        tier=self.tier,
                        title=title,
                        url=url,
                        posted_date=posted_date,
                        category=category,
                    ))
            except Exception as e:
                print(f"[{self.source_id}] {category} 수집 실패: {e}")
                continue

        return notices
