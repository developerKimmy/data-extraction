"""AIHub ZIP에서 schema 기반 텍스트 추출."""
import json
import zipfile
from collections import Counter
from datetime import datetime

from config import (
    DATASET_ID, DATASET_NAME,
    AIHUB_RAW_DIR, OUTPUT_DIR, ZIP_PREFIXES,
    SCHEMA, DEDUP_PREFIX_LEN, SMTP_CFG,
)
from shared import save_json, notify_error, notify_progress


def _resolve_field(obj, path):
    """점(.) 구분 경로로 중첩 필드 접근. 'doc_class.code' → obj['doc_class']['code']"""
    for key in path.split("."):
        if isinstance(obj, dict):
            obj = obj.get(key, "")
        else:
            return ""
    return obj


def _extract_from_zip(zip_path, schema):
    """ZIP 안의 JSON에서 schema에 따라 텍스트 추출. ZIP 오류 시 빈 리스트."""
    items_key = schema.get("items_key", "data")
    sub_list_key = schema.get("sub_list_key")
    text_key = schema.get("text_key", "context")
    metadata_map = schema.get("metadata", {})

    try:
        zf = zipfile.ZipFile(zip_path)
    except (zipfile.BadZipFile, OSError) as e:
        print(f"  ⚠ ZIP 열기 실패: {e}")
        return []

    results = []
    with zf:
        json_names = [n for n in zf.namelist() if n.endswith(".json")]

        for name in json_names:
            try:
                with zf.open(name) as f:
                    raw = f.read().decode("utf-8")
                    data = json.loads(raw, strict=False)
            except (json.JSONDecodeError, UnicodeDecodeError, KeyError) as e:
                print(f"  ⚠ 파싱 실패: {name} ({e})")
                continue

            items = data.get(items_key, []) if isinstance(data, dict) else data

            for item in items:
                targets = item.get(sub_list_key, []) if sub_list_key else [item]

                for target in targets:
                    text = target.get(text_key, "").strip()
                    if not text:
                        continue
                    entry = {"text": text}
                    for out_key, src_path in metadata_map.items():
                        entry[out_key] = _resolve_field(item, src_path)
                    results.append(entry)

    return results


def _dedup(entries, seen, prefix_len):
    """텍스트 앞 N자 기준 중복 제거. (신규 리스트, 추가 건수) 반환."""
    results = []
    for entry in entries:
        key = entry["text"][:prefix_len]
        if key not in seen:
            seen.add(key)
            results.append(entry)
    return results, len(results)


def _save_progress(output_path, all_entries):
    """중간 저장."""
    save_json(output_path, {
        "total": len(all_entries),
        "entries": all_entries,
    })


def _print_stats(all_entries):
    """카테고리별 통계 출력."""
    counts = Counter(e.get("category") or "기타" for e in all_entries)
    print(f"\n총 {len(all_entries)}건 추출 완료")
    print("\n카테고리별:")
    for cat, count in counts.most_common():
        print(f"  {cat}: {count}건")


def run():
    """AIHub ZIP에서 텍스트 추출."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"aihub_{DATASET_ID}.json"

    zip_files = sorted(AIHUB_RAW_DIR.rglob("*.zip"))
    source_zips = [z for z in zip_files if z.name.startswith(ZIP_PREFIXES)]
    total_zips = len(source_zips)

    task_name = f"AIHub {DATASET_ID} 추출"
    print(f"{task_name} ({datetime.now().strftime('%Y-%m-%d %H:%M')})")
    print(f"데이터셋: {DATASET_NAME}")
    print(f"대상 ZIP 파일: {total_zips}개")
    print("=" * 60)

    if total_zips == 0:
        print(f"\n⚠ ZIP 파일 없음. 경로를 확인하세요: {AIHUB_RAW_DIR}")
        return

    all_entries = []
    seen = set()
    fail_count = 0
    notified_half = False

    for i, zip_path in enumerate(source_zips):
        rel = zip_path.relative_to(AIHUB_RAW_DIR)
        print(f"\n▶ [{i+1}/{total_zips}] {rel}")

        entries = _extract_from_zip(zip_path, SCHEMA)

        if not entries:
            fail_count += 1
            notify_error(SMTP_CFG, task_name, f"ZIP 추출 실패: {rel}")
            continue

        new_items, added = _dedup(entries, seen, DEDUP_PREFIX_LEN)
        all_entries.extend(new_items)

        print(f"  추출: {len(entries)}건, 신규: {added}건 (누적: {len(all_entries)}건)")
        _save_progress(output_path, all_entries)

        if not notified_half and (i + 1) >= total_zips // 2:
            notified_half = True
            notify_progress(
                SMTP_CFG, task_name,
                i + 1, total_zips,
                extra=f"누적: {len(all_entries)}건, 실패: {fail_count}건",
            )

    _save_progress(output_path, all_entries)
    _print_stats(all_entries)
    print(f"\n저장: {output_path}")

    if fail_count:
        print(f"\n⚠ 실패한 ZIP: {fail_count}개")
