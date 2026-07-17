"""
모든 데이터 소스의 기본 클래스와 Notice 데이터 구조.
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
    posted_date: str
    category: str = ""

    def unique_id(self) -> str:
        return f"{self.source_id}::{self.title}::{self.posted_date}"

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
