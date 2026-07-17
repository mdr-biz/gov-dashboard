"""
메인 실행 스크립트.
GitHub Actions가 매일 오전 8시에 실행.

흐름:
  1. config.yaml 읽기
  2. 사이트별 크롤링
  3. 기존 아카이브(archive.json)와 병합 → 중복 제거
  4. HTML 대시보드 생성 → docs/index.html
  5. 아카이브 갱신 저장
"""
import json
import yaml
from pathlib import Path
from typing import List, Dict
from datetime import datetime

from sources import get_source
from sources.base import Notice
from dashboard import build_dashboard


ROOT = Path(__file__).parent
CONFIG_PATH = ROOT / "config.yaml"
ARCHIVE_PATH = ROOT / "archive.json"
OUTPUT_PATH = ROOT / "docs" / "index.html"


def load_config() -> dict:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_archive() -> Dict[str, dict]:
    """기존 아카이브 로드 (unique_id → notice dict)"""
    if ARCHIVE_PATH.exists():
        with open(ARCHIVE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_archive(archive: Dict[str, dict]):
    with open(ARCHIVE_PATH, "w", encoding="utf-8") as f:
        json.dump(archive, f, ensure_ascii=False, indent=2)


def main():
    config = load_config()
    archive = load_archive()

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
                    fresh_count += 1
                    d = n.to_dict()
                    d["_first_seen"] = datetime.now().strftime("%Y-%m-%d")
                    archive[uid] = d
        except Exception as e:
            print(f"   ❌ 실패: {e}")

    print(f"\n📬 새로 추가된 공지: {fresh_count}건")
    print(f"📚 전체 아카이브: {len(archive)}건")

    # 아카이브 크기 제한 (오래된 것부터 제거)
    max_archive = config.get("max_archive", 500)
    if len(archive) > max_archive:
        sorted_items = sorted(
            archive.items(),
            key=lambda x: x[1].get("posted_date", "") or x[1].get("_first_seen", ""),
            reverse=True,
        )
        archive = dict(sorted_items[:max_archive])

    # Notice 객체로 변환
    all_notices = []
    for d in archive.values():
        all_notices.append(Notice(
            source_id=d["source_id"],
            source_name=d["source_name"],
            tier=d["tier"],
            title=d["title"],
            url=d["url"],
            posted_date=d.get("posted_date", ""),
            category=d.get("category", ""),
        ))

    # 대시보드 생성
    html = build_dashboard(
        notices=all_notices,
        title=config["dashboard_title"],
        highlight_days=config.get("highlight_days", 3),
    )

    OUTPUT_PATH.parent.mkdir(exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✅ 대시보드 생성 완료: {OUTPUT_PATH}")

    save_archive(archive)
    print(f"✅ 아카이브 저장 완료")


if __name__ == "__main__":
    main()
