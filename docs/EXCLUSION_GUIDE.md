# 제외 종목 관리 가이드

특정 종목을 AI 추천에서 영구적으로 제외하고 싶을 때 사용하는 기능입니다.

## 📋 개요

제외 종목 관리 시스템은 다음과 같은 경우에 유용합니다:

- **리스크가 높은 종목**: 변동성이 너무 크거나 불안정한 종목
- **투자 정책 위반**: 특정 산업군이나 테마 제외 (예: 도박, 담배)
- **개인적 선호**: 특정 기업에 투자하고 싶지 않은 경우
- **법적/윤리적 이유**: ESG, 사회적 책임 투자 기준
- **테스트 목적**: 일시적으로 특정 종목 제외

## 🔧 사용 방법

### 1. 제외 종목 목록 조회

```bash
# 현재 제외된 종목 목록 확인
python3 paper_trading/manage_exclusions.py list
```

**출력 예시**:
```
================================================================================
제외 종목 목록 (2개)
================================================================================

[035420] NAVER
  섹터: IT서비스
  사유: 높은 변동성
  제외일: 2025-10-23T10:00:00
  제외자: cli
  메모: 단기 트레이딩에 부적합

[005380] 현대차
  섹터: 자동차
  사유: 업종 제외 정책
  제외일: 2025-10-22T15:30:00
  제외자: user
```

### 2. 제외 종목 추가

```bash
# 기본 사용법
python3 paper_trading/manage_exclusions.py add [종목코드] "[제외 사유]"

# 예시
python3 paper_trading/manage_exclusions.py add 035420 "높은 변동성"

# 메모 추가 (선택)
python3 paper_trading/manage_exclusions.py add 035420 "높은 변동성" --notes "단기 트레이딩에 부적합"
```

**출력**:
```
제외 종목 추가: 035420
사유: 높은 변동성
메모: 단기 트레이딩에 부적합

✅ 제외 종목 추가: 035420 (ID: 1)

✅ 제외 종목이 추가되었습니다.
   다음 AI 분석부터 이 종목은 추천에서 제외됩니다.
```

### 3. 제외 종목 해제

```bash
# 제외 해제
python3 paper_trading/manage_exclusions.py remove [종목코드]

# 예시
python3 paper_trading/manage_exclusions.py remove 035420
```

**출력**:
```
제외 종목 해제: 035420

✅ 제외 종목 해제: 035420

✅ 제외 종목이 해제되었습니다.
   다음 AI 분석부터 이 종목은 다시 추천될 수 있습니다.
```

### 4. 제외 여부 확인

```bash
# 특정 종목이 제외되었는지 확인
python3 paper_trading/manage_exclusions.py check [종목코드]

# 예시
python3 paper_trading/manage_exclusions.py check 005930
```

**출력 (제외된 경우)**:
```
❌ 005930는 제외 종목입니다.

종목명: 삼성전자
섹터: 반도체
사유: 테스트용 제외
제외일: 2025-10-23T10:00:00
제외자: cli
```

**출력 (제외되지 않은 경우)**:
```
✅ 005930는 제외 종목이 아닙니다. 정상적으로 추천될 수 있습니다.
```

## 🗄️ 데이터베이스 초기화

처음 제외 종목 기능을 사용할 때 데이터베이스 테이블을 초기화해야 합니다:

```bash
python3 paper_trading/manage_exclusions.py init-db
```

**출력**:
```
⚠️  제외 종목 테이블을 초기화합니다...
   기존 데이터는 유지되며, 테이블이 없는 경우에만 생성됩니다.

✅ 제외 종목 테이블 초기화 완료
```

**참고**:
- 이 명령은 테이블이 없을 때만 생성하며, 기존 데이터를 삭제하지 않습니다
- PostgreSQL에 `excluded_stocks` 테이블을 생성합니다
- 관련 뷰와 함수도 함께 생성됩니다

## 🔄 AI 분석 워크플로에서 자동 필터링

제외 종목은 Paper Trading 실행 시 자동으로 필터링됩니다:

### 워크플로 단계

1. **AI 분석 실행**: 모든 종목 대상으로 분석
2. **추천 종목 생성**: AI가 3~10개 종목 추천
3. **제외 종목 필터링**: 제외 목록과 비교하여 자동 제거
4. **비중 재조정**: 남은 종목들의 비중을 재계산 (합계 100%)
5. **매수 실행**: 필터링된 종목만 매수

### 실행 예시

```bash
# Paper Trading 실행
./paper_trading/run_paper_trading.sh
```

**출력**:
```
[Step 3] AI 투자 분석
------------------------------------------------------------
...

📊 AI 추천 종목 (3개):
   • 005930: 33.3%
   • 035420: 33.3%
   • 000660: 33.3%

🔍 제외 종목 필터링 중...
ℹ️  제외된 종목: 035420
   ⚠️  1개 종목이 제외 목록으로 인해 필터링되었습니다

✅ 최종 추천 종목 (2개):
   • 005930: 50.0%
   • 000660: 50.0%
```

## 💡 사용 시나리오

### 시나리오 1: 변동성이 높은 종목 제외

```bash
# 바이오 종목 제외 (예시)
python3 paper_trading/manage_exclusions.py add 326030 "극심한 변동성" --notes "바이오 테마주"
python3 paper_trading/manage_exclusions.py add 214450 "극심한 변동성" --notes "바이오 테마주"
```

### 시나리오 2: 특정 업종 제외

```bash
# 건설 업종 제외
python3 paper_trading/manage_exclusions.py add 000720 "업종 제외 정책" --notes "건설업"
python3 paper_trading/manage_exclusions.py add 028050 "업종 제외 정책" --notes "건설업"
```

### 시나리오 3: 일시적 제외 후 복원

```bash
# 테스트를 위해 일시 제외
python3 paper_trading/manage_exclusions.py add 005930 "테스트용 제외"

# ... 테스트 진행 ...

# 테스트 완료 후 복원
python3 paper_trading/manage_exclusions.py remove 005930
```

### 시나리오 4: 대량 종목 제외 (스크립트)

여러 종목을 한 번에 제외하려면 쉘 스크립트 작성:

```bash
#!/bin/bash
# exclude_multiple.sh

STOCKS=(
    "005380:자동차업종:제외 정책"
    "012330:자동차업종:제외 정책"
    "000270:건설업종:제외 정책"
)

for stock in "${STOCKS[@]}"; do
    IFS=':' read -r code reason notes <<< "$stock"
    python3 paper_trading/manage_exclusions.py add "$code" "$reason" --notes "$notes"
done
```

실행:
```bash
chmod +x exclude_multiple.sh
./exclude_multiple.sh
```

## 📊 데이터베이스 구조

제외 종목은 PostgreSQL 데이터베이스에 저장됩니다:

### 테이블: `excluded_stocks`

| 컬럼 | 타입 | 설명 |
|------|------|------|
| exclusion_id | SERIAL | 기본 키 |
| code | VARCHAR(10) | 종목 코드 (UNIQUE) |
| name | VARCHAR(100) | 종목명 |
| reason | TEXT | 제외 사유 (필수) |
| excluded_by | VARCHAR(50) | 제외 주체 (cli, user 등) |
| excluded_at | TIMESTAMP | 제외 일시 |
| is_active | BOOLEAN | 활성 상태 (TRUE: 제외 중, FALSE: 해제됨) |
| notes | TEXT | 추가 메모 |

### 뷰: `v_excluded_stocks`

제외된 종목 정보를 `stocks` 테이블과 조인하여 보여줍니다.

### 함수

- `is_stock_excluded(code)`: 특정 종목이 제외되었는지 확인
- `filter_excluded_stocks(codes[])`: 종목 배열에서 제외 종목 제거
- `add_excluded_stock(...)`: 제외 종목 추가
- `remove_excluded_stock(code)`: 제외 종목 해제

## 🔌 Python API 사용

스크립트나 프로그램에서 직접 사용:

```python
from core.utils.exclusion_manager import (
    add_excluded_stock,
    remove_excluded_stock,
    is_stock_excluded,
    get_excluded_stocks,
    filter_excluded_recommendations
)

# 제외 종목 추가
add_excluded_stock("035420", "높은 변동성", excluded_by="system", notes="자동 감지")

# 제외 여부 확인
if is_stock_excluded("035420"):
    print("이 종목은 제외되었습니다")

# 추천 결과 필터링
recommendations = [
    {'code': '005930', 'weight': 0.33},
    {'code': '035420', 'weight': 0.33},  # 제외됨
    {'code': '000660', 'weight': 0.34}
]

filtered = filter_excluded_recommendations(recommendations)
# 결과: [{'code': '005930', 'weight': 0.5}, {'code': '000660', 'weight': 0.5}]

# 전체 제외 종목 조회
excluded = get_excluded_stocks()
for stock in excluded:
    print(f"{stock['code']}: {stock['stock_name']}")

# 제외 해제
remove_excluded_stock("035420")
```

## ⚠️ 주의사항

### 1. 제외 종목은 즉시 반영됨

제외 종목을 추가하면 **다음 AI 분석부터 즉시 적용**됩니다.
- 이미 보유 중인 종목은 자동으로 매도되지 않습니다
- 새로운 매수 추천에서만 제외됩니다

### 2. 보유 중인 종목을 제외하는 경우

보유 중인 종목을 제외 목록에 추가해도:
- 기존 포지션은 유지됩니다
- 손절/익절 조건은 여전히 적용됩니다
- 추가 매수만 방지됩니다

강제로 매도하려면:
```bash
# Paper Trading 포트폴리오에서 수동 매도 필요
python3 paper_trading/manual_trade.py sell 035420 [수량]
```

### 3. 데이터베이스 백업

제외 종목 데이터는 PostgreSQL에 저장되므로 정기적인 백업 권장:

```bash
# 제외 종목 테이블만 백업
pg_dump -h localhost -U invest_user -d investment_db \
  -t excluded_stocks > excluded_stocks_backup.sql

# 복원
psql -h localhost -U invest_user -d investment_db < excluded_stocks_backup.sql
```

### 4. 중복 제외

같은 종목을 여러 번 제외하려고 하면:
- 기존 제외 정보가 **업데이트**됩니다
- 새로운 사유와 메모로 대체됩니다
- 제외 일시가 갱신됩니다

## 🔍 문제 해결

### 문제 1: "제외 종목 테이블이 없습니다"

**오류**:
```
ERROR: relation "excluded_stocks" does not exist
```

**해결**:
```bash
python3 paper_trading/manage_exclusions.py init-db
```

### 문제 2: "종목 코드가 유효하지 않습니다"

**원인**: `stocks` 테이블에 해당 종목이 없음

**해결**:
```bash
# 주가 데이터 수집으로 종목 정보 업데이트
python3 core/data/collect_stock_data.py
```

### 문제 3: 제외했는데 여전히 추천됨

**확인 사항**:
1. 제외 종목이 정말 추가되었는지 확인:
   ```bash
   python3 paper_trading/manage_exclusions.py list
   ```

2. Paper Trading 로그 확인:
   ```bash
   cat paper_trading/logs/trading_*.log | grep "제외 종목"
   ```

3. 데이터베이스 직접 확인:
   ```bash
   psql -h localhost -U invest_user -d investment_db \
     -c "SELECT * FROM excluded_stocks WHERE is_active = TRUE;"
   ```

## 📚 관련 파일

- **CLI 도구**: `paper_trading/manage_exclusions.py`
- **Python 유틸리티**: `core/utils/exclusion_manager.py`
- **데이터베이스 스키마**: `paper_trading/schema_exclusion.sql`
- **Paper Trading 워크플로**: `paper_trading/trading_crew.py`

## 💡 팁

### 자동 제외 정책 구현

특정 조건을 만족하는 종목을 자동으로 제외하는 스크립트 예시:

```python
# auto_exclude_volatile.py
from core.utils.exclusion_manager import add_excluded_stock
import psycopg2
import os

# 최근 30일 변동성이 50% 이상인 종목 제외
conn = psycopg2.connect(...)
cur = conn.cursor()

cur.execute("""
    SELECT code, name
    FROM stocks s
    JOIN (
        SELECT code,
               STDDEV(close_price) / AVG(close_price) as volatility
        FROM stock_prices
        WHERE date >= CURRENT_DATE - INTERVAL '30 days'
        GROUP BY code
    ) v ON s.code = v.code
    WHERE v.volatility > 0.5
""")

for code, name in cur.fetchall():
    add_excluded_stock(
        code,
        "높은 변동성 (자동 감지)",
        excluded_by="system",
        notes=f"30일 변동성 50% 초과"
    )
```

### 제외 종목 리포트

제외 종목 현황을 정기적으로 리포트:

```bash
# 제외 종목 리포트 생성
python3 paper_trading/manage_exclusions.py list > excluded_stocks_report.txt

# 이메일로 전송 (선택)
mail -s "제외 종목 리포트" your-email@gmail.com < excluded_stocks_report.txt
```
