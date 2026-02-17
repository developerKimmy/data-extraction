"""AIHub 데이터 추출 설정."""
import os
from pathlib import Path

from dotenv import load_dotenv

import __init__  # noqa: F401 — sys.path 설정
from shared import load_config

_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_ENV_PATH)

BASE_DIR = Path(__file__).parent
PROJECT_ROOT = BASE_DIR.parent
CONFIG_JSON = BASE_DIR / "config.json"
DATA_DIR = BASE_DIR.parent / "data"
OUTPUT_DIR = DATA_DIR / "output"

_DEFAULTS = {
    "dataset": {
        "id": "017",
        "name": "뉴스 기사 기계독해 데이터",
        "raw_path": "",
        "zip_prefixes": ["TS_", "VS_"],
    },
    "schema": {
        "items_key": "data",
        "sub_list_key": "paragraphs",
        "text_key": "context",
        "metadata": {},
    },
    "dedup_prefix_len": 200,
}
_CFG = load_config(CONFIG_JSON, _DEFAULTS)

DATASET = _CFG["dataset"]
DATASET_ID = DATASET["id"]
DATASET_NAME = DATASET["name"]
AIHUB_RAW_DIR = PROJECT_ROOT / DATASET["raw_path"]
ZIP_PREFIXES = tuple(DATASET["zip_prefixes"])

SCHEMA = _CFG["schema"]
DEDUP_PREFIX_LEN = _CFG["dedup_prefix_len"]

_SMTP_ENABLED = os.getenv("SMTP_ENABLED", "false").lower() == "true"
SMTP_CFG = {
    "host": os.getenv("SMTP_HOST", "smtp.gmail.com"),
    "port": int(os.getenv("SMTP_PORT", "587")),
    "user": os.getenv("SMTP_USER", ""),
    "password": os.getenv("SMTP_PASSWORD", ""),
    "to": os.getenv("SMTP_TO", ""),
} if _SMTP_ENABLED else None
