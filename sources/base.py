"""
모든 데이터 소스의 기본 클래스와 Notice 데이터 구조.

날짜 필드 설계:
  - posted_date: 공고 작성일/등록일/게시일 (소스가 제공하는 가장 정확한 "올라온 날")
  - 없으면 접수시작일, 그것도 없으면 빈 값
  - 빈 값일 때는 main.py에서 _first_seen(우리가 처음 본 날)으로 보완
"""
from dataclasses import dataclass, asdict
from typing import List
import requests


@dataclass
class Notice:
    source_id: str
    source_name: str
    tier: int
    title: str
    url: str
    posted_date: str        # 공고 작성일/등록일 (YYYY-MM-DD)
    category: str = ""
    date_basis: str = ""    # 이 날짜가 무엇인지 표시용 (작성일/접수일/수집일)

    def unique_id(self) -> str:
        return f"{self.source_id}::{self.title}"

    def to_dict(self):
        return asdict(self)


class BaseSource:
    source_id: str = ""
    source_name: str = ""
    tier: int = 0

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json",
        })

    def fetch(self) -> List[Notice]:
        raise NotImplementedError
