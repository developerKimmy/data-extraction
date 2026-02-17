"""디코딩된 URL에서 본문 추출 로직"""
import sys
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

import __init__  # noqa: F401 — sys.path 설정
from config import CATEGORIES, DECODED_DIR, OUTPUT_DIR, SMTP_CFG
from utils import save_json, load_items_with_keys, extract_article
from shared import notify_progress


def _extract_one(item):
    """단일 기사 본문 추출. 실패 시 None."""
    content = extract_article(item["url"])
    if content is None:
        return None
    return {
        "original_title": item.get("title", ""),
        "source": item.get("source", ""),
        "published": item.get("published", ""),
        "url": item["url"],
        "google_link": item.get("google_link", ""),
        **content,
    }


def _extract_batch(batch, workers, done_urls):
    """배치 하나를 병렬 추출. (성공 리스트, 실패 수) 반환."""
    successes = []
    fail = 0
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(_extract_one, item): item for item in batch}
        for f in as_completed(futures):
            try:
                result = f.result()
                if result and result["url"] not in done_urls:
                    successes.append(result)
                    done_urls.add(result["url"])
                else:
                    fail += 1
            except Exception:
                fail += 1
    return successes, fail


def extract_category(category_code, workers):
    """카테고리 하나의 디코딩된 URL에서 본문 추출."""
    config = CATEGORIES[category_code]
    name = config["name"]
    decoded_path = DECODED_DIR / f"{category_code.lower()}.json"
    output_path = OUTPUT_DIR / f"{category_code.lower()}.json"

    decoded_items, _ = load_items_with_keys(decoded_path, list_key=None, dedup_key="url")
    if not decoded_items:
        print(f"  ✗ {name}: 디코딩 데이터 없음")
        return []

    results, done_urls = load_items_with_keys(output_path, list_key=None, dedup_key="url")
    todo = [item for item in decoded_items if item["url"] not in done_urls]

    print(f"\n▶ {name} ({category_code}) - 기존 {len(results)}건, 신규 {len(todo)}건")

    total_success = total_fail = 0
    batch_size = workers * 3
    notified_half = False

    for batch_start in range(0, len(todo), batch_size):
        batch = todo[batch_start:batch_start + batch_size]
        successes, fail = _extract_batch(batch, workers, done_urls)

        for item in successes:
            item["category"] = category_code
            item["category_ko"] = name
            results.append(item)
        total_success += len(successes)
        total_fail += fail

        processed = min(batch_start + batch_size, len(todo))
        sys.stdout.write(f"\r  추출 {processed}/{len(todo)} (성공: {total_success}, 실패: {total_fail})")
        sys.stdout.flush()

        if not notified_half and processed >= len(todo) // 2:
            notified_half = True
            notify_progress(
                SMTP_CFG, f"본문 추출 - {name}",
                processed, len(todo),
                extra=f"성공: {total_success}, 실패: {total_fail}",
            )

        if processed % 50 == 0 or processed >= len(todo):
            save_json(output_path, results)

    save_json(output_path, results)
    print(f"\n  ✓ {name}: {len(results)}건 (신규 +{total_success}건)")
    return results


def run(categories, workers):
    """본문 추출 실행."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    codes = [c for c in categories if c in CATEGORIES]

    print(f"본문 추출 시작 ({datetime.now().strftime('%Y-%m-%d %H:%M')}, 워커 {workers}개)")

    all_results = {}
    for code in codes:
        all_results[code] = extract_category(code, workers)

    total = sum(len(v) for v in all_results.values())
    save_json(OUTPUT_DIR / "all_articles.json", {
        "collected_at": datetime.now().isoformat(),
        "total_articles": total,
        "articles": [a for arts in all_results.values() for a in arts],
    })
    print(f"\n전체 완료: {total}건")
