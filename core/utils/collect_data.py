"""한국 주식 데이터 수집 스크립트"""

import FinanceDataReader as fdr
import pandas as pd
from datetime import datetime, timedelta
from db_utils import (
    get_db_connection,
    insert_stocks_batch,
    insert_prices_batch,
    get_stock_list
)


def collect_stock_list(market='KOSPI', limit=None):
    """
    주식 종목 리스트 수집 및 저장

    Args:
        market: 'KOSPI', 'KOSDAQ', 또는 'ALL'
        limit: 상위 N개만 수집 (None이면 전체)

    Returns:
        int: 저장된 종목 수
    """
    print("=" * 60)
    print(f"종목 리스트 수집 시작 (시장: {market})")
    print("=" * 60)

    try:
        # KRX 전체 종목 가져오기
        krx_stocks = fdr.StockListing('KRX')

        # 시장 필터링
        if market == 'KOSPI':
            stocks = krx_stocks[krx_stocks['Market'] == 'KOSPI']
        elif market == 'KOSDAQ':
            stocks = krx_stocks[krx_stocks['Market'] == 'KOSDAQ']
        else:
            stocks = krx_stocks

        # 상위 N개만 선택
        if limit:
            stocks = stocks.head(limit)

        print(f"✓ 조회된 종목 수: {len(stocks)}")

        # 데이터베이스에 저장할 형식으로 변환
        # Sector 컬럼이 없는 경우를 대비해 처리
        stocks_data = []
        for _, row in stocks.iterrows():
            code = row['Code']
            name = row['Name']
            market_val = row.get('Market', 'UNKNOWN')
            sector = row.get('Sector', row.get('Industry', 'N/A'))  # Sector 또는 Industry 사용

            stocks_data.append((code, name, market_val, sector))

        # 일괄 삽입
        affected_rows = insert_stocks_batch(stocks_data)
        print(f"✓ 데이터베이스 저장 완료: {affected_rows}개 종목")

        # 샘플 출력
        print("\n저장된 종목 샘플 (상위 10개):")
        for i, (code, name, market_val, sector) in enumerate(stocks_data[:10], 1):
            print(f"  {i:2d}. {name:15s} ({code}) - {sector}")

        return affected_rows

    except Exception as e:
        print(f"✗ 종목 리스트 수집 실패: {e}")
        import traceback
        traceback.print_exc()
        return 0


def collect_price_data(days=30, limit_stocks=None):
    """
    주식 가격 데이터 수집

    Args:
        days: 최근 N일간 데이터 수집
        limit_stocks: 상위 N개 종목만 수집 (None이면 전체)

    Returns:
        tuple: (성공 수, 실패 수)
    """
    print("\n" + "=" * 60)
    print(f"가격 데이터 수집 시작 (최근 {days}일)")
    print("=" * 60)

    # 데이터베이스에서 종목 리스트 가져오기
    stocks = get_stock_list(limit=limit_stocks)
    print(f"수집 대상 종목: {len(stocks)}개")

    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    print(f"기간: {start_date.date()} ~ {end_date.date()}\n")

    success_count = 0
    fail_count = 0
    total_rows = 0

    for idx, (code, name, sector) in enumerate(stocks, 1):
        try:
            # FinanceDataReader로 가격 데이터 가져오기
            df = fdr.DataReader(code, start_date, end_date)

            if len(df) == 0:
                print(f"[{idx:3d}/{len(stocks)}] ⚠ {name:15s} ({code}) - 데이터 없음")
                fail_count += 1
                continue

            # 데이터베이스 저장 형식으로 변환
            prices_data = []
            for date, row in df.iterrows():
                prices_data.append((
                    code,
                    date.date(),
                    float(row['Open']),
                    float(row['High']),
                    float(row['Low']),
                    float(row['Close']),
                    int(row['Volume'])
                ))

            # 일괄 삽입
            insert_prices_batch(prices_data)
            total_rows += len(prices_data)
            success_count += 1

            print(f"[{idx:3d}/{len(stocks)}] ✓ {name:15s} ({code}) - {len(df):3d} rows")

        except Exception as e:
            print(f"[{idx:3d}/{len(stocks)}] ✗ {name:15s} ({code}) - 에러: {e}")
            fail_count += 1

    print("\n" + "-" * 60)
    print(f"수집 완료: 성공 {success_count}, 실패 {fail_count}")
    print(f"총 저장된 데이터: {total_rows:,} rows")
    print("=" * 60)

    return success_count, fail_count


def verify_data():
    """수집된 데이터 검증"""
    print("\n" + "=" * 60)
    print("데이터 검증")
    print("=" * 60)

    conn = get_db_connection()
    cur = conn.cursor()

    # 종목 수
    cur.execute("SELECT COUNT(*) FROM stocks;")
    stock_count = cur.fetchone()[0]
    print(f"종목 수: {stock_count:,}")

    # 가격 데이터 수
    cur.execute("SELECT COUNT(*) FROM prices;")
    price_count = cur.fetchone()[0]
    print(f"가격 데이터: {price_count:,} rows")

    # 날짜 범위
    cur.execute("SELECT MIN(date), MAX(date) FROM prices;")
    date_range = cur.fetchone()
    if date_range[0]:
        print(f"날짜 범위: {date_range[0]} ~ {date_range[1]}")

    # 섹터별 종목 수
    cur.execute("""
        SELECT sector, COUNT(*) as cnt
        FROM stocks
        GROUP BY sector
        ORDER BY cnt DESC
        LIMIT 5;
    """)
    sectors = cur.fetchall()
    print("\n섹터별 종목 수 (상위 5개):")
    for sector, cnt in sectors:
        print(f"  {sector:20s}: {cnt:3d}개")

    # 최근 거래일 데이터
    cur.execute("""
        SELECT s.name, p.date, p.close, p.volume
        FROM prices p
        JOIN stocks s ON p.code = s.code
        ORDER BY p.date DESC, p.volume DESC
        LIMIT 5;
    """)
    recent = cur.fetchall()
    print("\n최근 거래 데이터 (거래량 상위):")
    for name, date, close, volume in recent:
        print(f"  {name:15s} | {date} | {close:>10,.0f}원 | {volume:>12,} 주")

    cur.close()
    conn.close()
    print("=" * 60)


def main():
    """메인 실행 함수"""
    print("\n" + "=" * 70)
    print(" " * 20 + "한국 주식 데이터 수집")
    print("=" * 70)
    print(f"시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # 1. 종목 리스트 수집 (코스피 상위 50개로 테스트)
    stock_count = collect_stock_list(market='KOSPI', limit=50)

    if stock_count == 0:
        print("\n종목 리스트 수집 실패. 프로그램을 종료합니다.")
        return

    # 2. 가격 데이터 수집 (최근 30일)
    success, fail = collect_price_data(days=30, limit_stocks=50)

    # 3. 데이터 검증
    verify_data()

    # 4. 완료 메시지
    print("\n" + "=" * 70)
    print(f"종료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)


if __name__ == "__main__":
    main()
