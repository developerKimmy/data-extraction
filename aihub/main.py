"""AIHub 데이터 추출 진입점."""
import argparse

import __init__  # noqa: F401 — sys.path 설정
from extract import run as run_extract


def build_parser():
    parser = argparse.ArgumentParser(description="AIHub 뉴스 데이터 추출")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("extract", help="ZIP에서 본문 추출")

    return parser


def main():
    args = build_parser().parse_args()

    if args.command == "extract":
        run_extract()


if __name__ == "__main__":
    main()
