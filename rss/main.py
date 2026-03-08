"""RSS 뉴스 파이프라인 진입점 (collect / decode / extract)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import argparse
from config import ACTIVE_CATEGORIES, TARGET_PER_CATEGORY, EXTRACT_WORKERS
from collect import run as run_collect
from decode import run as run_decode
from extract import run as run_extract


def build_parser():
    parser = argparse.ArgumentParser(description="RSS 뉴스 파이프라인")
    sub = parser.add_subparsers(dest="command", required=True)

    p_collect = sub.add_parser("collect", help="RSS 기사 링크 수집")
    p_collect.add_argument(
        "--categories", nargs="+", default=ACTIVE_CATEGORIES,
        help="수집할 카테고리 코드",
    )
    p_collect.add_argument(
        "--target", type=int, default=TARGET_PER_CATEGORY,
        help=f"카테고리당 목표 건수 (기본: {TARGET_PER_CATEGORY})",
    )

    p_decode = sub.add_parser("decode", help="Google News URL 디코딩")
    p_decode.add_argument(
        "--categories", nargs="+", default=ACTIVE_CATEGORIES,
        help="대상 카테고리 코드",
    )

    p_extract = sub.add_parser("extract", help="본문 추출")
    p_extract.add_argument(
        "--categories", nargs="+", default=ACTIVE_CATEGORIES,
        help="대상 카테고리 코드",
    )
    p_extract.add_argument(
        "--workers", type=int, default=EXTRACT_WORKERS,
        help=f"병렬 워커 수 (기본: {EXTRACT_WORKERS})",
    )

    return parser


def main():
    args = build_parser().parse_args()

    if args.command == "collect":
        run_collect(args.categories, args.target)
    elif args.command == "decode":
        run_decode(args.categories)
    elif args.command == "extract":
        run_extract(args.categories, args.workers)


if __name__ == "__main__":
    main()
