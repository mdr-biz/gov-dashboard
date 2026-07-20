"""
크롤러 등록소.
"""
from .bizinfo import BizinfoSource
from .datago import KStartupSource, MssSource, MsitSource
from .sba import SbaSource
from .kiria import KiriaSource


API_SOURCES = {
    "bizinfo": BizinfoSource,
    "kstartup": KStartupSource,
    "mss": MssSource,
    "msit": MsitSource,
    "sba": SbaSource,        # HTML 크롤링이지만 registry엔 여기 포함
    "kiria": KiriaSource,
}


def get_source(source_id: str):
    if source_id in API_SOURCES:
        return API_SOURCES[source_id]()
    return None
