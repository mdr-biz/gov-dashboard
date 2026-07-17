"""
기업마당(BizInfo) 크롤러 - 수정판.
- 응답 키는 'jsonArray' (대문자 A)
- crtfcKey(무료 API 인증키) 필요 → 환경변수 BIZINFO_KEY 로 주입
"""
import os
from typing import List
from .base import BaseSource, Notice


class BizinfoSource(BaseSource):
    source_id = "bizinfo"
    source_name = "기업마당"
    tier = 1

    API_URL = "https://www.bizinfo.go.kr/uss/rss/bizinfoApi.do"

    def fetch(self) -> List[Notice]:
        notices: List[Notice] = []

        api_key = os.environ.get("BIZINFO_KEY", "").strip()
        if not api_key:
            print(f"[{self.source_id}] BIZINFO_KEY 환경변수 없음 - 건너뜀 "
                  f"(무료 키 발급 후 GitHub Secrets에 등록하세요)")
            return notices

        try:
            params = {
                "crtfcKey": api_key,
                "dataType": "json",
                "searchCnt": "100",
            }
            resp = self.session.get(self.API_URL, params=params, timeout=20)
            data = resp.json()

            if isinstance(data, dict) and data.get("reqErr"):
                print(f"[{self.source_id}] API 오류: {data.get('reqErr')}")
                return notices

            items = []
            if isinstance(data, dict):
                items = data.get("jsonArray", []) or data.get("jsonarray", [])
            elif isinstance(data, list):
                items = data

            for item in items:
                title = (item.get("pblancNm") or "").strip()
                if not title:
                    continue

                detail_url = item.get("pblancUrl", "") or ""
                if detail_url.startswith("/"):
                    url = "https://www.bizinfo.go.kr" + detail_url
                elif detail_url.startswith("http"):
                    url = detail_url
                else:
                    url = "https://www.bizinfo.go.kr/web/lay1/bbs/S1T122C128/AS/74/list.do"

                posted = (item.get("creatPnttm") or item.get("regDt") or "")[:10]
                category = item.get("pldirSportRealmLclasCodeNm") or "지원사업"

                notices.append(Notice(
                    source_id=self.source_id,
                    source_name=self.source_name,
                    tier=self.tier,
                    title=title,
                    url=url,
                    posted_date=posted,
                    category=category,
                ))
        except Exception as e:
            print(f"[{self.source_id}] 수집 실패: {e}")

        return notices
