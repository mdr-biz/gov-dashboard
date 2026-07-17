"""
기업마당(BizInfo) 크롤러.
공개 JSON API 사용 - 인증키 불필요.
560여개 지원기관의 지원사업 공고를 한 번에 수집.
"""
from typing import List
from .base import BaseSource, Notice


class BizinfoSource(BaseSource):
    source_id = "bizinfo"
    source_name = "기업마당"
    tier = 1

    API_URL = "https://www.bizinfo.go.kr/uss/rss/bizinfoApi.do"

    def fetch(self) -> List[Notice]:
        notices: List[Notice] = []
        try:
            # dataType=json 으로 요청하면 JSON 반환
            params = {"dataType": "json"}
            resp = self.session.get(self.API_URL, params=params, timeout=20)
            data = resp.json()

            # 응답 구조: {"jsonarray": [ {...}, {...} ]}
            items = data.get("jsonarray", [])

            for item in items:
                title = item.get("pblancNm", "").strip()
                if not title:
                    continue

                # 상세 URL 조합
                detail_url = item.get("pblancUrl", "")
                if detail_url.startswith("/"):
                    url = "https://www.bizinfo.go.kr" + detail_url
                elif detail_url.startswith("http"):
                    url = detail_url
                else:
                    url = "https://www.bizinfo.go.kr/web/lay1/bbs/S1T122C128/AS/74/list.do"

                # 등록일 (creatPnttm 또는 regDt 형태)
                posted = item.get("creatPnttm", "") or item.get("regDt", "")
                posted = posted[:10] if posted else ""

                # 분야를 카테고리로
                category = item.get("pldirSportRealmLclasCodeNm", "") or "지원사업"

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
