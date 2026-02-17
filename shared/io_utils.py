"""JSON I/O 유틸리티"""
import json
from copy import deepcopy
from pathlib import Path


def load_json(path):
    """JSON 파일 로드. 없으면 None."""
    path = Path(path)
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    """JSON 파일 저장 (상위 디렉토리 자동 생성)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_config(config_path, defaults=None):
    """config.json 로드 후 defaults와 병합."""
    result = deepcopy(defaults) if defaults else {}
    data = load_json(config_path)
    if data:
        result.update(data)
    return result


def load_items_with_keys(path, list_key="articles", dedup_key="link"):
    """JSON에서 리스트 + 중복 체크용 set 추출."""
    data = load_json(path)
    if data is None:
        return [], set()

    if list_key and isinstance(data, dict):
        items = data.get(list_key, [])
    elif isinstance(data, list):
        items = data
    else:
        return [], set()

    seen = {item.get(dedup_key, "") for item in items}
    return items, seen
