#!/usr/bin/env python3
"""
제외 종목 관리 CLI 도구

사용법:
  python manage_exclusions.py list                                    # 제외 종목 목록 조회
  python manage_exclusions.py add 005930 "테스트용 제외"               # 종목 제외
  python manage_exclusions.py remove 005930                           # 제외 해제
  python manage_exclusions.py check 005930                            # 제외 여부 확인
"""

import sys
import argparse
from pathlib import Path

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from core.utils.exclusion_manager import (
    add_excluded_stock,
    remove_excluded_stock,
    is_stock_excluded,
    get_excluded_stocks,
    print_excluded_stocks
)


def cmd_list(args):
    """제외 종목 목록 조회"""
    print_excluded_stocks()


def cmd_add(args):
    """제외 종목 추가"""
    code = args.code
    reason = args.reason
    notes = args.notes

    print(f"\n제외 종목 추가: {code}")
    print(f"사유: {reason}")
    if notes:
        print(f"메모: {notes}")
    print()

    success = add_excluded_stock(code, reason, excluded_by="cli", notes=notes)

    if success:
        print("\n✅ 제외 종목이 추가되었습니다.")
        print("   다음 AI 분석부터 이 종목은 추천에서 제외됩니다.\n")
    else:
        print("\n❌ 제외 종목 추가에 실패했습니다.\n")
        sys.exit(1)


def cmd_remove(args):
    """제외 종목 해제"""
    code = args.code

    print(f"\n제외 종목 해제: {code}\n")

    success = remove_excluded_stock(code)

    if success:
        print("\n✅ 제외 종목이 해제되었습니다.")
        print("   다음 AI 분석부터 이 종목은 다시 추천될 수 있습니다.\n")
    else:
        print("\n⚠️  제외 종목이 아니거나 이미 해제되었습니다.\n")


def cmd_check(args):
    """제외 여부 확인"""
    code = args.code

    excluded = is_stock_excluded(code)

    if excluded:
        print(f"\n❌ {code}는 제외 종목입니다.\n")

        # 상세 정보 조회
        excluded_stocks = get_excluded_stocks()
        for stock in excluded_stocks:
            if stock['code'] == code:
                print(f"종목명: {stock.get('stock_name', 'N/A')}")
                print(f"섹터: {stock.get('sector', 'N/A')}")
                print(f"사유: {stock.get('reason', 'N/A')}")
                print(f"제외일: {stock.get('excluded_at', 'N/A')}")
                print(f"제외자: {stock.get('excluded_by', 'N/A')}")
                if stock.get('notes'):
                    print(f"메모: {stock['notes']}")
                print()
                break
    else:
        print(f"\n✅ {code}는 제외 종목이 아닙니다. 정상적으로 추천될 수 있습니다.\n")


def cmd_init_db(args):
    """데이터베이스 테이블 초기화"""
    import os
    import psycopg2

    print("\n⚠️  제외 종목 테이블을 초기화합니다...")
    print("   기존 데이터는 유지되며, 테이블이 없는 경우에만 생성됩니다.\n")

    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432"),
            database=os.getenv("DB_NAME", "investment_db"),
            user=os.getenv("DB_USER", "invest_user"),
            password=os.getenv("DB_PASSWORD", "invest_pass_2024!")
        )

        # schema_exclusion.sql 실행
        schema_file = Path(__file__).parent / "schema_exclusion.sql"
        with open(schema_file, 'r', encoding='utf-8') as f:
            schema_sql = f.read()

        cur = conn.cursor()
        cur.execute(schema_sql)
        conn.commit()
        cur.close()
        conn.close()

        print("✅ 제외 종목 테이블 초기화 완료\n")

    except Exception as e:
        print(f"❌ 테이블 초기화 실패: {e}\n")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="제외 종목 관리 CLI 도구",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  %(prog)s list                                    # 제외 종목 목록 조회
  %(prog)s add 005930 "테스트용 제외"               # 종목 제외
  %(prog)s add 005930 "리스크 높음" --notes "추가 메모"  # 메모 포함
  %(prog)s remove 005930                           # 제외 해제
  %(prog)s check 005930                            # 제외 여부 확인
  %(prog)s init-db                                 # 데이터베이스 초기화
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='명령어')

    # list 명령
    parser_list = subparsers.add_parser('list', help='제외 종목 목록 조회')
    parser_list.set_defaults(func=cmd_list)

    # add 명령
    parser_add = subparsers.add_parser('add', help='제외 종목 추가')
    parser_add.add_argument('code', help='종목 코드 (예: 005930)')
    parser_add.add_argument('reason', help='제외 사유')
    parser_add.add_argument('--notes', help='추가 메모', default=None)
    parser_add.set_defaults(func=cmd_add)

    # remove 명령
    parser_remove = subparsers.add_parser('remove', help='제외 종목 해제')
    parser_remove.add_argument('code', help='종목 코드 (예: 005930)')
    parser_remove.set_defaults(func=cmd_remove)

    # check 명령
    parser_check = subparsers.add_parser('check', help='제외 여부 확인')
    parser_check.add_argument('code', help='종목 코드 (예: 005930)')
    parser_check.set_defaults(func=cmd_check)

    # init-db 명령
    parser_init = subparsers.add_parser('init-db', help='데이터베이스 테이블 초기화')
    parser_init.set_defaults(func=cmd_init_db)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    # 명령 실행
    args.func(args)


if __name__ == "__main__":
    main()
