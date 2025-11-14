"""데이터베이스 스키마 설정 스크립트"""

import sys
from pathlib import Path

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from core.utils.db_utils import get_db_connection


def apply_schema():
    """스키마 파일을 읽어서 데이터베이스에 적용"""
    schema_file = Path(__file__).parent / "schema.sql"

    with open(schema_file, 'r', encoding='utf-8') as f:
        schema_sql = f.read()

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # SQL 파일 실행
        cur.execute(schema_sql)
        conn.commit()
        print("✅ 스키마 적용 완료")

        # 생성된 테이블 확인
        cur.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name LIKE 'virtual%'
            ORDER BY table_name;
        """)

        tables = cur.fetchall()
        print(f"\n📋 생성된 테이블 ({len(tables)}개):")
        for table in tables:
            print(f"   - {table[0]}")

    except Exception as e:
        print(f"❌ 스키마 적용 실패: {e}")
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


def create_initial_account(name: str = "AI 투자 시뮬레이션 #1",
                          initial_balance: float = 10_000_000):
    """초기 가상계좌 생성"""
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            INSERT INTO virtual_accounts (account_name, initial_balance, current_balance)
            VALUES (%s, %s, %s)
            RETURNING account_id, account_name, initial_balance
        """, (name, initial_balance, initial_balance))

        row = cur.fetchone()
        conn.commit()

        print(f"\n✅ 가상계좌 생성 완료")
        print(f"   계좌 ID: {row[0]}")
        print(f"   계좌명: {row[1]}")
        print(f"   초기 자금: {row[2]:,.0f}원")

        return row[0]

    except Exception as e:
        print(f"❌ 계좌 생성 실패: {e}")
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    print("=" * 60)
    print("페이퍼 트레이딩 시스템 초기화")
    print("=" * 60)

    # 1. 스키마 적용
    print("\n[1/2] 데이터베이스 스키마 적용 중...")
    apply_schema()

    # 2. 초기 계좌 생성
    print("\n[2/2] 초기 가상계좌 생성 중...")
    account_id = create_initial_account()

    print("\n" + "=" * 60)
    print("✅ 초기화 완료!")
    print(f"   생성된 계좌 ID: {account_id}")
    print("=" * 60)
