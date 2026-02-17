"""RSS 피드 수집 유틸리티"""
import feedparser
from datetime import datetime, timedelta


def generate_date_ranges(days=30, step=5):
    """최근 N일을 step 단위로 나눈 날짜 범위 리스트 반환."""
    ranges = []
    today = datetime.now()
    for i in range(0, days, step):
        end = today - timedelta(days=i)
        start = today - timedelta(days=i + step)
        ranges.append((start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")))
    return ranges


def fetch_rss(url):
    """RSS 피드 URL에서 기사 메타데이터 리스트 추출."""
    feed = feedparser.parse(url)
    articles = []
    for entry in feed.entries:
        articles.append({
            "title": entry.get("title", ""),
            "link": entry.get("link", ""),
            "published": entry.get("published", ""),
            "source": (
                entry.get("source", {}).get("title", "")
                if "source" in entry
                else ""
            ),
        })
    return articles
