"""PostgreSQL 데이터베이스 연결 유틸리티"""

import os
import psycopg2
from psycopg2.extras import execute_batch
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()


def get_db_connection():
    """PostgreSQL 연결 생성"""
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        database=os.getenv("DB_NAME", "investment_db"),
        user=os.getenv("DB_USER", "invest_user"),
        password=os.getenv("DB_PASSWORD")
    )


def test_connection():
    """데이터베이스 연결 테스트"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # PostgreSQL 버전 확인
        cur.execute("SELECT version();")
        version = cur.fetchone()[0]
        print(f"✓ PostgreSQL 연결 성공")
        print(f"  버전: {version.split(',')[0]}")

        # 테이블 목록 확인
        cur.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        tables = cur.fetchall()
        print(f"  테이블: {', '.join([t[0] for t in tables])}")

        # 데이터 통계
        cur.execute("SELECT COUNT(*) FROM stocks;")
        stock_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM prices;")
        price_count = cur.fetchone()[0]
        print(f"  데이터: stocks({stock_count}), prices({price_count})")

        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"✗ 데이터베이스 연결 실패: {e}")
        return False


def get_stock_list(limit=None):
    """데이터베이스에서 종목 리스트 조회"""
    conn = get_db_connection()
    cur = conn.cursor()

    query = "SELECT code, name, sector FROM stocks ORDER BY code"
    if limit:
        query += f" LIMIT {limit}"

    cur.execute(query)
    stocks = cur.fetchall()

    cur.close()
    conn.close()

    return stocks


def insert_stocks_batch(stocks_data):
    """
    종목 데이터 일괄 삽입/업데이트

    Args:
        stocks_data: [(code, name, market, sector), ...] 형태의 리스트

    Returns:
        int: 삽입/업데이트된 행 수
    """
    conn = get_db_connection()
    cur = conn.cursor()

    query = """
        INSERT INTO stocks (code, name, market, sector, updated_at)
        VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
        ON CONFLICT (code) DO UPDATE
        SET name = EXCLUDED.name,
            sector = EXCLUDED.sector,
            market = EXCLUDED.market,
            updated_at = EXCLUDED.updated_at
    """

    execute_batch(cur, query, stocks_data)
    conn.commit()

    affected_rows = cur.rowcount
    cur.close()
    conn.close()

    return affected_rows


def insert_prices_batch(prices_data):
    """
    가격 데이터 일괄 삽입/업데이트

    Args:
        prices_data: [(code, date, open, high, low, close, volume), ...] 형태의 리스트

    Returns:
        int: 삽입/업데이트된 행 수
    """
    conn = get_db_connection()
    cur = conn.cursor()

    query = """
        INSERT INTO prices (code, date, open, high, low, close, volume)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (code, date) DO UPDATE
        SET open = EXCLUDED.open,
            high = EXCLUDED.high,
            low = EXCLUDED.low,
            close = EXCLUDED.close,
            volume = EXCLUDED.volume
    """

    execute_batch(cur, query, prices_data, page_size=1000)
    conn.commit()

    affected_rows = cur.rowcount
    cur.close()
    conn.close()

    return affected_rows


if __name__ == "__main__":
    """스크립트 직접 실행 시 연결 테스트"""
    print("=" * 60)
    print("데이터베이스 연결 테스트")
    print("=" * 60)
    test_connection()
    print("=" * 60)
