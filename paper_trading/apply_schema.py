#!/usr/bin/env python3
"""
투자 룰 스키마 적용 스크립트
"""

import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.utils.db_utils import get_db_connection


def apply_schema(schema_file):
    """SQL 스키마 파일을 데이터베이스에 적용"""
    print("=" * 60)
    print("투자 룰 스키마 적용")
    print("=" * 60)

    # SQL 파일 읽기
    with open(schema_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()

    # DB 연결 및 실행
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            try:
                print(f"\n📄 SQL 파일: {schema_file}")
                print(f"📊 크기: {len(sql_content)} bytes\n")

                # SQL 실행
                cur.execute(sql_content)
                conn.commit()

                print("✅ 스키마 적용 성공!")

                # 생성된 테이블 확인
                cur.execute("""
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                      AND table_name IN ('investment_rules', 'rule_executions', 'dca_schedules',
                                         'rebalancing_history', 'realtime_price_cache')
                    ORDER BY table_name
                """)
                tables = cur.fetchall()

                print("\n생성된 테이블:")
                for table in tables:
                    print(f"  ✓ {table[0]}")

                # 뷰 확인
                cur.execute("""
                    SELECT table_name
                    FROM information_schema.views
                    WHERE table_schema = 'public'
                      AND table_name LIKE 'v_%rule%'
                    ORDER BY table_name
                """)
                views = cur.fetchall()

                print("\n생성된 뷰:")
                for view in views:
                    print(f"  ✓ {view[0]}")

                # 샘플 룰 확인
                cur.execute("SELECT COUNT(*) FROM investment_rules WHERE is_active = true")
                rule_count = cur.fetchone()[0]
                print(f"\n등록된 투자 룰: {rule_count}개")

                if rule_count > 0:
                    cur.execute("""
                        SELECT rule_id, rule_name, rule_type, asset_category
                        FROM investment_rules
                        WHERE is_active = true
                        ORDER BY priority, rule_id
                    """)
                    rules = cur.fetchall()
                    print("\n투자 룰 목록:")
                    for rule in rules:
                        print(f"  [{rule[0]}] {rule[1]} ({rule[2]}, {rule[3]})")

            except Exception as e:
                conn.rollback()
                print(f"\n❌ 오류 발생: {e}")
                raise

    print("\n" + "=" * 60)
    print("스키마 적용 완료")
    print("=" * 60)


if __name__ == "__main__":
    schema_path = os.path.join(
        os.path.dirname(__file__),
        "investment_rules_schema.sql"
    )

    if not os.path.exists(schema_path):
        print(f"❌ 스키마 파일을 찾을 수 없습니다: {schema_path}")
        sys.exit(1)

    try:
        apply_schema(schema_path)
    except Exception as e:
        print(f"\n❌ 스키마 적용 실패: {e}")
        sys.exit(1)
