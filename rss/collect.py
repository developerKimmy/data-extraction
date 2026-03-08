"""Google News RSS 기사 링크 수집 로직"""
import sys
import time
from datetime import datetime

from config import (
    CATEGORIES,
    RSS_DIR,
    DATE_RANGE_DAYS,
    DATE_RANGE_STEP,
    BASE_SEARCH_URL,
    BASE_TOPIC_URL,
    SMTP_CFG,
)
from utils import save_json, load_items_with_keys, fetch_rss, generate_date_ranges
from shared import notify_error, notify_progress

MAX_CONSECUTIVE_FAILS = 5
FAIL_WAIT_SECONDS = 30


def _collect_from_feed(url, articles, seen, limit):
    """RSS 피드에서 미수집 기사를 추가. 추가된 건수 반환."""
    try:
        feed = fetch_rss(url)
    except Exception as e:
        print(f"    ⚠ 피드 요청 실패: {e}")
        return 0

    added = 0
    for a in feed:
        if len(articles) >= limit:
            break
        if a["link"] not in seen:
            articles.append(a)
            seen.add(a["link"])
            added += 1
    return added


def _search_by_keyword(keyword, articles, seen, target):
    """키워드 검색 → 키워드+날짜 검색 순으로 수집."""
    query = keyword.replace(" ", "+")
    added = _collect_from_feed(BASE_SEARCH_URL.format(query=query), articles, seen, target)
    time.sleep(0.3)

    if len(articles) >= target:
        return added

    for start, end in generate_date_ranges(days=DATE_RANGE_DAYS, step=DATE_RANGE_STEP):
        if len(articles) >= target:
            break
        date_query = f"{query}+after:{start}+before:{end}"
        added += _collect_from_feed(BASE_SEARCH_URL.format(query=date_query), articles, seen, target)
        time.sleep(0.3)

    return added


def _save_progress(topic_code, config, articles):
    """중간 저장."""
    save_json(RSS_DIR / f"{topic_code.lower()}.json", {
        "category_ko": config["name"],
        "count": len(articles),
        "articles": articles,
    })


def collect_category(topic_code, config, target):
    """카테고리 하나에 대해 target건 수집. 키워드마다 중간 저장."""
    name = config["name"]
    rss_path = RSS_DIR / f"{topic_code.lower()}.json"
    articles, seen = load_items_with_keys(rss_path)
    initial = len(articles)
    notified_half = initial >= target // 2

    print(f"\n▶ {name} ({topic_code}) - 기존 {initial}건, 목표 {target}건")

    _collect_from_feed(BASE_TOPIC_URL.format(topic=topic_code), articles, seen, target)

    consecutive_fails = 0
    for keyword in config["keywords"]:
        if len(articles) >= target:
            break

        added = _search_by_keyword(keyword, articles, seen, target)

        if added:
            consecutive_fails = 0
            sys.stdout.write(f"  \"{keyword}\": +{added}건 (누적: {len(articles)}건)\n")
            sys.stdout.flush()
            _save_progress(topic_code, config, articles)
        else:
            consecutive_fails += 1

        if not notified_half and len(articles) >= target // 2:
            notified_half = True
            notify_progress(
                SMTP_CFG, f"RSS 수집 - {name}",
                len(articles), target,
                extra=f"키워드: {keyword}",
            )

        if consecutive_fails >= MAX_CONSECUTIVE_FAILS:
            print(f"    ⏳ 연속 {MAX_CONSECUTIVE_FAILS}회 실패, {FAIL_WAIT_SECONDS}초 대기...")
            _save_progress(topic_code, config, articles)
            notify_error(
                SMTP_CFG, f"RSS 수집 - {name}",
                f"연속 {MAX_CONSECUTIVE_FAILS}회 실패 (누적: {len(articles)}/{target}건)",
            )
            time.sleep(FAIL_WAIT_SECONDS)
            consecutive_fails = 0

    _save_progress(topic_code, config, articles)

    final = len(articles[:target])
    print(f"  ✓ {name} 완료: {final}건 (+{final - initial}건)")
    return articles[:target]


def run(categories, target):
    """수집 실행."""
    RSS_DIR.mkdir(parents=True, exist_ok=True)

    print(f"RSS 수집 시작 ({datetime.now().strftime('%Y-%m-%d %H:%M')})")
    print(f"대상: {len(categories)}개 카테고리, 목표: 카테고리당 {target}건")

    total = 0
    for code in categories:
        if code not in CATEGORIES:
            print(f"  ✗ 알 수 없는 카테고리: {code}")
            continue
        articles = collect_category(code, CATEGORIES[code], target)
        total += len(articles)

    print(f"\n전체 수집 완료: {total}건")


