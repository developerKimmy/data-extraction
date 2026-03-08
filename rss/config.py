"""RSS 뉴스 수집 설정."""
import os
from pathlib import Path

from dotenv import load_dotenv

from utils import load_json, load_config

load_dotenv()

BASE_DIR = Path(__file__).parent
CONFIG_JSON = BASE_DIR / "config.json"
DATA_DIR = BASE_DIR.parent / "data"
RSS_DIR = DATA_DIR / "rss" / "links"
DECODED_DIR = DATA_DIR / "rss" / "urls"
OUTPUT_DIR = DATA_DIR / "rss" / "articles"

_DEFAULTS = {
    "target_per_category": 500,
    "extract_workers": 5,
    "categories": ["WORLD", "NATION", "BUSINESS", "TECHNOLOGY",
                    "ENTERTAINMENT", "SCIENCE", "SPORTS", "HEALTH"],
    "date_range": {"days": 30, "step": 5},
}
_CFG = load_config(CONFIG_JSON, _DEFAULTS)

TARGET_PER_CATEGORY = _CFG["target_per_category"]
EXTRACT_WORKERS = _CFG["extract_workers"]
ACTIVE_CATEGORIES = _CFG["categories"]
DATE_RANGE_DAYS = _CFG["date_range"]["days"]
DATE_RANGE_STEP = _CFG["date_range"]["step"]

_SMTP_ENABLED = os.getenv("SMTP_ENABLED", "false").lower() == "true"
SMTP_CFG = {
    "host": os.getenv("SMTP_HOST", "smtp.gmail.com"),
    "port": int(os.getenv("SMTP_PORT", "587")),
    "user": os.getenv("SMTP_USER", ""),
    "password": os.getenv("SMTP_PASSWORD", ""),
    "to": os.getenv("SMTP_TO", ""),
} if _SMTP_ENABLED else None

BASE_SEARCH_URL = "https://news.google.com/rss/search?q={query}&hl=ko&gl=KR&ceid=KR:ko"
BASE_TOPIC_URL = "https://news.google.com/rss/headlines/section/topic/{topic}?hl=ko&gl=KR&ceid=KR:ko"

CATEGORIES = load_json(BASE_DIR / "categories.json") or {}
