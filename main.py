"""
메인 실행 스크립트 - 작성일 기준 개편판.

핵심 로직:
  1. 각 소스에서 공고 수집 (posted_date = 작성일/등록일 우선)
  2. 아카이브와 대조:
     - 처음 보는 공고면 _first_seen = 오늘 로 기록
  3. effective_date(정렬·알림 기준일) 결정:
     - posted_date가 있으면 그것을 사용
     - 없으면 _first_seen 사용 (우리가 처음 수집한 날)
  4. effective_date 기준 최신순 정렬 → 대시보드 생성
  5. 3일 이내 새 공고 목록을 별도 파일(recent.json)로 저장 → 이메일용
"""
import json
import yaml
from pathlib import Path
from typing import List, Dict
from datetime import datetime, timedelta

from sources import get_source
from sources.base import Notice
from dashboard import build_dashboard


ROOT = Path(__file__).parent
CONFIG_PATH = ROOT / "config.yaml"
ARCHIVE_PATH = ROOT / "archive.json"
OUTPUT_PATH = ROOT / "docs" / "index.html"
RECENT_PATH = ROOT / "recent.json"   # 이메일 발송용 (최근 N일 새 공고)


def load_config() -> dict:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_archive() -> Dict[str, dict]:
    if ARCHIVE_PATH.exists():
        with open(ARCHIVE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_archive(archive: Dict[str, dict]):
    with open(ARCHIVE_PATH, "w", encoding="utf-8") as f:
        json.dump(archive, f, ensure_ascii=False, indent=2)


def effective_date(rec: dict) -> str:
    """정렬·알림 기준일: 작성일 우선, 없으면 처음 수집한 날"""
    return rec.get("posted_date") or rec.get("_first_seen") or ""


def main():
    config = load_config()
    archive = load_archive()
    today = datetime.now().strftime("%Y-%m-%d")

    fresh_count = 0

    for src_cfg in config["sources"]:
        if not src_cfg.get("enabled", True):
            continue
        source_id = src_cfg["id"]
        source = get_source(source_id)
        if source is None:
            print(f"⚠️  {src_cfg['name']} ({source_id}) 크롤러 미구현 - 건너뜀")
            continue

        print(f"🔍 {src_cfg['name']} 수집 중...")
        try:
            notices = source.fetch()
            print(f"   → {len(notices)}건 수집")
            for n in notices:
                uid = n.unique_id()
                if uid not in archive:
                    # 처음 보는 공고
                    fresh_count += 1
                    d = n.to_dict()
                    d["_first_seen"] = today
                    archive[uid] = d
                else:
                    # 이미 있는 공고 - posted_date가 새로 채워졌으면 업데이트
                    existing = archive[uid]
                    if not existing.get("posted_date") and n.posted_date:
                        existing["posted_date"] = n.posted_date
                        existing["date_basis"] = n.date_basis
        except Exception as e:
            print(f"   ❌ 실패: {e}")

    print(f"\n📬 이번에 새로 발견: {fresh_count}건")
    print(f"📚 전체 아카이브: {len(archive)}건")

    # 아카이브 크기 제한 (effective_date 최신순 유지)
    max_archive = config.get("max_archive", 500)
    if len(archive) > max_archive:
        sorted_items = sorted(archive.items(),
                              key=lambda x: effective_date(x[1]), reverse=True)
        archive = dict(sorted_items[:max_archive])

    # Notice 객체 목록으로 변환 (effective_date를 posted_date로 주입)
    all_notices = []
    for d in archive.values():
        eff = effective_date(d)
        basis = d.get("date_basis") or ("작성일" if d.get("posted_date") else "수집일")
        all_notices.append(Notice(
            source_id=d["source_id"], source_name=d["source_name"],
            tier=d["tier"], title=d["title"], url=d["url"],
            posted_date=eff, category=d.get("category", ""),
            date_basis=basis,
        ))

    # 대시보드 생성 (내부에서 effective_date 기준 정렬)
    html = build_dashboard(
        notices=all_notices,
        title=config["dashboard_title"],
        highlight_days=config.get("highlight_days", 3),
    )
    OUTPUT_PATH.parent.mkdir(exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✅ 대시보드 생성 완료")

    # --- 이메일용: 최근 N일 새 공고 저장 ---
    highlight_days = config.get("highlight_days", 3)
    cutoff = (datetime.now() - timedelta(days=highlight_days)).strftime("%Y-%m-%d")
    recent = [n.to_dict() for n in all_notices if n.posted_date >= cutoff]
    # 최신순 정렬
    recent.sort(key=lambda x: x.get("posted_date", ""), reverse=True)
    with open(RECENT_PATH, "w", encoding="utf-8") as f:
        json.dump({
            "generated": today,
            "cutoff": cutoff,
            "highlight_days": highlight_days,
            "count": len(recent),
            "notices": recent,
        }, f, ensure_ascii=False, indent=2)
    print(f"✅ 최근 {highlight_days}일 새 공고: {len(recent)}건 (recent.json)")

    save_archive(archive)
    print(f"✅ 아카이브 저장 완료")


if __name__ == "__main__":
    main()
