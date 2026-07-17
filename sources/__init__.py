"""
크롤러 등록소.
- bizinfo: 전용 JSON API 크롤러
- 나머지: 범용 게시판 크롤러(GenericBoardSource) 사용
"""
from .bizinfo import BizinfoSource
from .generic import GenericBoardSource, GENERIC_BOARDS


def get_source(source_id: str):
    """config.yaml의 id로 적절한 크롤러 인스턴스를 반환"""
    if source_id == "bizinfo":
        return BizinfoSource()
    if source_id in GENERIC_BOARDS:
        return GenericBoardSource(source_id)
    # 아직 미구현 사이트 (kstartup, mss, at, kotra)
    return None
