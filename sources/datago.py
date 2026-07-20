"""
공공데이터포털(data.go.kr) API 크롤러들.
날짜는 "작성일/등록일" 우선, 없으면 접수시작일 사용.
"""
import os
import xml.etree.ElementTree as ET
from typing import List
from .base import BaseSource, Notice


def _get_key() -> str:
    return os.environ.get("DATAGO_KEY", "").strip()


def _fmt_date(s: str) -> str:
    """YYYYMMDD 또는 YYYY-MM-DD → YYYY-MM-DD"""
    s = (s or "").strip()
    if not s:
        return ""
    s = s.replace(".", "-").replace("/", "-")
    digits = s.replace("-", "")
    if len(digits) == 8 and digits.isdigit():
        return f"{digits[:4]}-{digits[4:6]}-{digits[6:8]}"
    return s[:10]


class KStartupSource(BaseSource):
    """창업진흥원 K-Startup 사업공고 (JSON)"""
    source_id = "kstartup"
    source_name = "K-Startup"
    tier = 1
    API_URL = "https://apis.data.go.kr/B552735/kisedKstartupService01/getAnnouncementInformation01"

    def fetch(self) -> List[Notice]:
        notices: List[Notice] = []
        key = _get_key()
        if not key:
            print(f"[{self.source_id}] DATAGO_KEY 없음 - 건너뜀")
            return notices
        try:
            params = {"serviceKey": key, "page": "1", "perPage": "100", "returnType": "json"}
            resp = self.session.get(self.API_URL, params=params, timeout=20)
            data = resp.json()
            items = data.get("data", []) or []
            for item in items:
                title = (item.get("biz_pbanc_nm") or item.get("intg_pbanc_biz_nm") or "").strip()
                if not title:
                    continue
                url = (item.get("detl_pg_url") or item.get("biz_pbanc_url")
                       or "https://www.k-startup.go.kr").strip()

                # 날짜 우선순위: 등록일 후보 → 접수시작일
                posted = ""
                basis = ""
                # 등록일 계열 필드 후보들 (여러 이름 시도)
                for f in ("creat_dt", "reg_dt", "rgst_dt", "creat_pnttm", "last_mdfcn_dt"):
                    if item.get(f):
                        posted = _fmt_date(item.get(f))
                        basis = "작성일"
                        break
                # 없으면 접수시작일
                if not posted:
                    posted = _fmt_date(item.get("pbanc_rcpt_bgng_dt", ""))
                    if posted:
                        basis = "접수시작일"

                category = (item.get("supt_biz_clsfc") or "창업지원").strip()
                notices.append(Notice(
                    source_id=self.source_id, source_name=self.source_name,
                    tier=self.tier, title=title, url=url,
                    posted_date=posted, category=category, date_basis=basis,
                ))
        except Exception as e:
            print(f"[{self.source_id}] 수집 실패: {e}")
        return notices


def _parse_xml_items(xml_text: str):
    root = ET.fromstring(xml_text)
    items = []
    for item in root.iter("item"):
        d = {}
        for child in item:
            d[child.tag] = (child.text or "").strip()
        items.append(d)
    return items


class MssSource(BaseSource):
    """중소벤처기업부 사업공고 (XML)"""
    source_id = "mss"
    source_name = "중소벤처기업부"
    tier = 1
    API_URL = "https://apis.data.go.kr/1421000/mssBiz/getbizList"

    def fetch(self) -> List[Notice]:
        notices: List[Notice] = []
        key = _get_key()
        if not key:
            print(f"[{self.source_id}] DATAGO_KEY 없음 - 건너뜀")
            return notices
        try:
            params = {"serviceKey": key, "pageNo": "1", "numOfRows": "100"}
            resp = self.session.get(self.API_URL, params=params, timeout=20)
            text = resp.text.strip()
            if not text.startswith("<"):
                print(f"[{self.source_id}] XML 아님: {text[:80]}")
                return notices
            items = _parse_xml_items(text)
            for item in items:
                title = (item.get("title") or item.get("bsnsTitle")
                         or item.get("pblancNm") or "").strip()
                if not title:
                    continue
                url = (item.get("url") or item.get("rfrncUrl")
                       or item.get("pblancUrl") or "https://www.mss.go.kr").strip()
                posted = _fmt_date(item.get("regDt") or item.get("rgstDt")
                                   or item.get("creatDt") or "")
                notices.append(Notice(
                    source_id=self.source_id, source_name=self.source_name,
                    tier=self.tier, title=title, url=url,
                    posted_date=posted, category="사업공고",
                    date_basis="작성일" if posted else "",
                ))
            if not items:
                print(f"[{self.source_id}] item 없음: {text[:150]}")
        except Exception as e:
            print(f"[{self.source_id}] 수집 실패: {e}")
        return notices


class MsitSource(BaseSource):
    """과학기술정보통신부 사업공고 (XML, R&D)"""
    source_id = "msit"
    source_name = "과학기술정보통신부"
    tier = 2
    API_URL = "https://apis.data.go.kr/1721000/msitannouncementinfo/businessAnnouncMentList"

    def fetch(self) -> List[Notice]:
        notices: List[Notice] = []
        key = _get_key()
        if not key:
            print(f"[{self.source_id}] DATAGO_KEY 없음 - 건너뜀")
            return notices
        try:
            params = {"serviceKey": key, "pageNo": "1", "numOfRows": "100"}
            resp = self.session.get(self.API_URL, params=params, timeout=20)
            text = resp.text.strip()
            if not text.startswith("<"):
                print(f"[{self.source_id}] XML 아님: {text[:80]}")
                return notices
            items = _parse_xml_items(text)
            for item in items:
                title = (item.get("title") or item.get("bsnsTitle")
                         or item.get("pblancNm") or "").strip()
                if not title:
                    continue
                url = (item.get("rfrncUrl") or item.get("detailUrl")
                       or item.get("url") or "https://www.msit.go.kr").strip()
                posted = _fmt_date(item.get("registDt") or item.get("regDt")
                                   or item.get("creatDt") or "")
                notices.append(Notice(
                    source_id=self.source_id, source_name=self.source_name,
                    tier=self.tier, title=title, url=url,
                    posted_date=posted, category="R&D 사업공고",
                    date_basis="작성일" if posted else "",
                ))
            if not items:
                print(f"[{self.source_id}] item 없음: {text[:150]}")
        except Exception as e:
            print(f"[{self.source_id}] 수집 실패: {e}")
        return notices
