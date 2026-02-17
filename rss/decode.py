"""Google News URL → 실제 URL 디코딩 로직"""
import sys
import time
from datetime import datetime

from googlenewsdecoder import gnewsdecoder

import __init__  # noqa: F401 — sys.path 설정
from config import CATEGORIES, RSS_DIR, DECODED_DIR, SMTP_CFG
from utils import save_json, load_items_with_keys
from shared import notify_error, notify_progress


def _decode_one(item):
    """Google News URL 하나를 실제 URL로 디코딩. 실패 시 None."""
    try:
        result = gnewsdecoder(item["link"], interval=None)
        if result.get("status"):
            return {
                "google_link": item["link"],
                "url": result["decoded_url"],
                "title": item.get("title", ""),
                "source": item.get("source", ""),
                "published": item.get("published", ""),
            }
    except Exception:
        pass
    return None


def _handle_rate_limit(consecutive_fail, decoded_path, results, name):
    """레이트 리밋 감지 시 대기 + 알림. 대기했으면 True."""
    if consecutive_fail not in (10, 20):
        return False
    wait = 60 if consecutive_fail == 10 else 120
    sys.stdout.write(f"\n  ⏳ 레이트 리밋, {wait}초 대기...\n")
    sys.stdout.flush()
    save_json(decoded_path, results)
    notify_error(
        SMTP_CFG, f"URL 디코딩 - {name}",
        f"레이트 리밋 감지 (연속 {consecutive_fail}회 실패, {wait}초 대기)",
    )
    time.sleep(wait)
    return True


def decode_category(category_code):
    """카테고리 하나의 Google News URL을 실제 URL로 디코딩."""
    config = CATEGORIES[category_code]
    name = config["name"]
    rss_path = RSS_DIR / f"{category_code.lower()}.json"
    decoded_path = DECODED_DIR / f"{category_code.lower()}.json"

    articles, _ = load_items_with_keys(rss_path)
    if not articles:
        print(f"  ✗ {name}: RSS 데이터 없음")
        return 0

    results, done = load_items_with_keys(decoded_path, list_key=None, dedup_key="google_link")
    todo = [a for a in articles if a["link"] not in done]

    print(f"\n▶ {name} ({category_code}) - 기존 {len(done)}건, 신규 {len(todo)}건")

    success = fail = consecutive_fail = 0
    notified_half = False

    for i, item in enumerate(todo):
        decoded = _decode_one(item)
        if decoded:
            results.append(decoded)
            success += 1
            consecutive_fail = 0
        else:
            fail += 1
            consecutive_fail += 1

        if _handle_rate_limit(consecutive_fail, decoded_path, results, name):
            consecutive_fail = 0

        if (i + 1) % 20 == 0:
            sys.stdout.write(f"\r  디코딩 {i+1}/{len(todo)} (성공: {success}, 실패: {fail})")
            sys.stdout.flush()
            save_json(decoded_path, results)

        if not notified_half and (i + 1) >= len(todo) // 2:
            notified_half = True
            notify_progress(
                SMTP_CFG, f"URL 디코딩 - {name}",
                i + 1, len(todo),
                extra=f"성공: {success}, 실패: {fail}",
            )

        time.sleep(0.5)

    save_json(decoded_path, results)
    print(f"\n  ✓ {name}: {len(results)}건 (신규 +{success}건)")
    return len(results)


def run(categories):
    """디코딩 실행."""
    DECODED_DIR.mkdir(parents=True, exist_ok=True)
    codes = [c for c in categories if c in CATEGORIES]

    print(f"URL 디코딩 시작 ({datetime.now().strftime('%Y-%m-%d %H:%M')})")

    for code in codes:
        decode_category(code)
