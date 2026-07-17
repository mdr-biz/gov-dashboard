"""
크롤러 등록소.
- 공공데이터포털 API 기반 (안정적): bizinfo, kstartup, mss, msit
- HTML 크롤링 (보조, 깨질 수 있음): generic board sources
"""
from .bizinfo import BizinfoSource
from .datago import KStartupSource, MssSource, MsitSource
from .generic import GenericBoardSource, GENERIC_BOARDS


# API 기반 소스 (우선)
API_SOURCES = {
    "bizinfo": BizinfoSource,
    "kstartup": KStartupSource,
    "mss": MssSource,
    "msit": MsitSource,
}


def get_source(source_id: str):
    if source_id in API_SOURCES:
        return API_SOURCES[source_id]()
    if source_id in GENERIC_BOARDS:
        return GenericBoardSource(source_id)
    return None
