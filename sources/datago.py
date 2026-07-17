"""
공공데이터포털(data.go.kr) 기반 API 크롤러들.
모두 하나의 인증키(DATAGO_KEY)를 공유해서 사용.

포함된 소스:
  - kstartup   : 창업진흥원 K-Startup 사업공고
  - mss        : 중소벤처기업부 사업공고
  - msit       : 과학기술정보통신부 사업공고 (R&D)
"""
import os
from typing import List
from .base import BaseSource, Notice


def _get_key() -> str:
    """
    공공데이터포털 인증키.
    Decoding 키(원본)를 넣는 것을 권장.
    requests가 자동으로 인코딩하므로 Decoding 키가 안전함.
    """
    return os.environ.get("DATAGO_KEY", "").strip()


class KStartupSource(BaseSource):
    """창업진흥원 K-Startup 사업공고"""
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
            params = {
                "serviceKey": key,
                "page": "1",
                "perPage": "100",
                "returnType": "json",
            }
            resp = self.session.get(self.API_URL, params=params, timeout=20)
            data = resp.json()

            items = data.get("data", []) or []
            for item in items:
                title = (item.get("biz_pbanc_nm") or item.get("intg_pbanc_biz_nm") or "").strip()
                if not title:
                    continue
                url = (item.get("detl_pg_url") or item.get("biz_pbanc_url")
                       or "https://www.k-startup.go.kr").strip()
                # 접수 시작일
                posted = (item.get("pbanc_rcpt_bgng_dt") or "").strip()
                if len(posted) == 8:  # YYYYMMDD
                    posted = f"{posted[:4]}-{posted[4:6]}-{posted[6:8]}"
                category = (item.get("supt_biz_clsfc") or "창업지원").strip()

                notices.append(Notice(
                    source_id=self.source_id, source_name=self.source_name,
                    tier=self.tier, title=title, url=url,
                    posted_date=posted, category=category,
                ))
        except Exception as e:
            print(f"[{self.source_id}] 수집 실패: {e}")
        return notices


class MssSource(BaseSource):
    """중소벤처기업부 사업공고"""
    source_id = "mss"
    source_name = "중소벤처기업부"
    tier = 1

    API_URL = "https://apis.data.go.kr/1421000/mssBizService/getbizList"

    def fetch(self) -> List[Notice]:
        notices: List[Notice] = []
        key = _get_key()
        if not key:
            print(f"[{self.source_id}] DATAGO_KEY 없음 - 건너뜀")
            return notices

        try:
            params = {
                "serviceKey": key,
                "pageNo": "1",
                "numOfRows": "100",
                "type": "json",
            }
            resp = self.session.get(self.API_URL, params=params, timeout=20)
            data = resp.json()

            # 응답 구조가 기관마다 다름 - 유연하게 파싱
            items = self._extract_items(data)
            for item in items:
                title = (item.get("title") or item.get("bsnsTitle") or "").strip()
                if not title:
                    continue
                url = (item.get("url") or item.get("rfrncUrl") or "").strip()
                if not url:
                    url = "https://www.mss.go.kr"
                posted = (item.get("regDt") or item.get("rgstDt") or "")[:10]
                notices.append(Notice(
                    source_id=self.source_id, source_name=self.source_name,
                    tier=self.tier, title=title, url=url,
                    posted_date=posted, category="사업공고",
                ))
        except Exception as e:
            print(f"[{self.source_id}] 수집 실패: {e}")
        return notices

    def _extract_items(self, data):
        """중첩된 응답에서 item 리스트를 찾아냄"""
        if isinstance(data, dict):
            # response > body > items > item 구조 탐색
            body = data.get("response", {}).get("body", {})
            items = body.get("items", {})
            if isinstance(items, dict):
                item = items.get("item", [])
                return item if isinstance(item, list) else [item]
            if isinstance(items, list):
                return items
            # 다른 구조
            if "data" in data:
                return data["data"]
        return []


class MsitSource(BaseSource):
    """과학기술정보통신부 사업공고 (R&D)"""
    source_id = "msit"
    source_name = "과학기술정보통신부"
    tier = 2  # R&D는 로봇 핵심 티어로

    API_URL = "https://apis.data.go.kr/1721000/msitannouncementinfo/businessAnnouncMentList"

    def fetch(self) -> List[Notice]:
        notices: List[Notice] = []
        key = _get_key()
        if not key:
            print(f"[{self.source_id}] DATAGO_KEY 없음 - 건너뜀")
            return notices

        try:
            params = {
                "serviceKey": key,
                "pageNo": "1",
                "numOfRows": "100",
                "type": "json",
            }
            resp = self.session.get(self.API_URL, params=params, timeout=20)
            data = resp.json()

            items = []
            if isinstance(data, dict):
                body = data.get("response", {}).get("body", {})
                its = body.get("items", {})
                if isinstance(its, dict):
                    it = its.get("item", [])
                    items = it if isinstance(it, list) else [it]
                elif isinstance(its, list):
                    items = its

            for item in items:
                title = (item.get("title") or item.get("bsnsTitle") or "").strip()
                if not title:
                    continue
                url = (item.get("rfrncUrl") or item.get("detailUrl") or "").strip()
                if not url:
                    url = "https://www.msit.go.kr"
                posted = (item.get("registDt") or item.get("regDt") or "")[:10]
                notices.append(Notice(
                    source_id=self.source_id, source_name=self.source_name,
                    tier=self.tier, title=title, url=url,
                    posted_date=posted, category="R&D 사업공고",
                ))
        except Exception as e:
            print(f"[{self.source_id}] 수집 실패: {e}")
        return notices
