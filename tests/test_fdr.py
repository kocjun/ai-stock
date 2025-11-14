"""FinanceDataReader 연동 테스트 스크립트"""

import FinanceDataReader as fdr
import pandas as pd
from datetime import datetime, timedelta

print("=" * 60)
print("FinanceDataReader 연동 테스트")
print("=" * 60)

# 1. 코스피 종목 리스트 조회
print("\n[1] 코스피 종목 리스트 조회")
print("-" * 60)
try:
    krx_stocks = fdr.StockListing('KRX')
    kospi = krx_stocks[krx_stocks['Market'] == 'KOSPI']
    print(f"✓ 전체 코스피 종목 수: {len(kospi)}")

    # 상위 10개 종목 출력
    print("\n샘플 종목 (상위 10개):")
    print(kospi[['Code', 'Name', 'Sector', 'Market']].head(10).to_string(index=False))
except Exception as e:
    print(f"✗ 종목 리스트 조회 실패: {e}")

# 2. 삼성전자 가격 데이터 조회
print("\n\n[2] 삼성전자(005930) 최근 1개월 가격 데이터")
print("-" * 60)
try:
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)

    samsung = fdr.DataReader('005930', start_date, end_date)
    print(f"✓ 조회된 데이터 행 수: {len(samsung)}")
    print(f"✓ 기간: {samsung.index[0].date()} ~ {samsung.index[-1].date()}")
    print("\n최근 5일 데이터:")
    print(samsung.tail(5).to_string())
except Exception as e:
    print(f"✗ 가격 데이터 조회 실패: {e}")

# 3. 여러 종목 수집 테스트
print("\n\n[3] 주요 종목 데이터 수집 테스트")
print("-" * 60)

test_stocks = [
    ('005930', '삼성전자'),
    ('000660', 'SK하이닉스'),
    ('035420', 'NAVER'),
    ('005380', '현대차'),
    ('051910', 'LG화학'),
    ('035720', '카카오'),
    ('006400', '삼성SDI'),
    ('000270', '기아'),
    ('068270', '셀트리온'),
    ('207940', '삼성바이오로직스')
]

success_count = 0
fail_count = 0
end_date = datetime.now()
start_date = end_date - timedelta(days=7)  # 최근 1주일

print(f"기간: {start_date.date()} ~ {end_date.date()}\n")

for code, name in test_stocks:
    try:
        df = fdr.DataReader(code, start_date, end_date)
        if len(df) > 0:
            latest_price = df['Close'].iloc[-1]
            print(f"✓ {name:12s} ({code}) : {len(df):2d} rows, 최근가 {latest_price:>10,.0f}원")
            success_count += 1
        else:
            print(f"⚠ {name:12s} ({code}) : 데이터 없음")
            fail_count += 1
    except Exception as e:
        print(f"✗ {name:12s} ({code}) : 에러 - {e}")
        fail_count += 1

# 4. 결과 요약
print("\n" + "=" * 60)
print("테스트 결과 요약")
print("=" * 60)
print(f"성공: {success_count} / 실패: {fail_count} / 총: {success_count + fail_count}")
print(f"성공률: {success_count / (success_count + fail_count) * 100:.1f}%")

if success_count >= 8:
    print("\n✓ FinanceDataReader 연동 정상 작동")
else:
    print("\n⚠ 일부 종목 데이터 수집 실패 - API 제한 또는 네트워크 확인 필요")

print("=" * 60)
