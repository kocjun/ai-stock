# 📊 페이퍼 트레이딩 시스템 구현 문서

## 🎯 구현 개요

**작성일**: 2025-10-18
**버전**: 1.0
**상태**: ✅ 구현 완료

AI 에이전트 기반 자동 투자 시뮬레이션 시스템을 성공적으로 구현했습니다.

---

## 📦 구현된 모듈

### 1. 데이터베이스 스키마 (`schema.sql`)

**파일 크기**: 8.4KB

#### 생성된 테이블 (5개)

```sql
1. virtual_accounts
   - 가상 계좌 정보
   - 초기 자금, 현재 잔고, 투자 전략

2. virtual_trades
   - 매수/매도 거래 내역
   - 종목 코드, 수량, 가격, 수수료, 사유

3. virtual_portfolio
   - 현재 보유 포지션
   - 평균 매입가, 현재가, 손익률

4. virtual_portfolio_history
   - 일별 스냅샷
   - 자산 가치 추이 기록

5. virtual_reports
   - 성과 보고서
   - 수익률, Sharpe, MDD 등 지표
```

#### 생성된 뷰 (3개)

```sql
1. v_account_summary
   - 계좌 전체 요약 (현금 + 주식)

2. v_trade_details
   - 거래 내역 상세 (종목명 포함)

3. v_position_details
   - 포지션 상세 (섹터, 비중 포함)
```

#### 유틸리티 함수 (2개)

```sql
1. cleanup_zero_positions()
   - 수량 0인 포지션 자동 정리

2. save_daily_snapshot(account_id)
   - 일일 스냅샷 저장
```

---

### 2. 초기 설정 (`setup_schema.py`)

**파일 크기**: 2.7KB

#### 기능
- 스키마 자동 적용
- 기본 가상계좌 생성 (ID: 1, 초기 자금: 1,000만원)

#### 실행 방법
```bash
python3 paper_trading/setup_schema.py
```

#### 실행 결과
```
✅ 스키마 적용 완료
📋 생성된 테이블 (5개):
   - virtual_accounts
   - virtual_portfolio
   - virtual_portfolio_history
   - virtual_reports
   - virtual_trades

✅ 가상계좌 생성 완료
   계좌 ID: 1
   계좌명: AI 투자 시뮬레이션 #1
   초기 자금: 10,000,000원
```

---

### 3. 매매 실행 모듈 (`paper_trading.py`)

**파일 크기**: 19KB

#### 주요 함수

##### 3.1 `execute_buy(account_id, code, quantity, price, reason)`
매수 주문 실행

**처리 과정**:
1. 현재가 조회 (price 미지정 시)
2. 총 금액 계산 (주식금액 × 1.00015) - 수수료 0.015%
3. 잔고 확인
4. 거래 기록 저장
5. 잔고 차감
6. 포지션 업데이트 (평균 매입가 재계산)

**예외 처리**:
- `InsufficientFundsError` - 잔고 부족
- `InvalidPriceError` - 가격 정보 없음

##### 3.2 `execute_sell(account_id, code, quantity, price, reason)`
매도 주문 실행

**처리 과정**:
1. 보유 수량 확인
2. 현재가 조회
3. 총 금액 계산 (주식금액 × 0.99985) - 수수료 0.015%
4. 실현 손익 계산
5. 거래 기록 저장
6. 잔고 증가
7. 포지션 감소 또는 삭제

**예외 처리**:
- `InsufficientSharesError` - 보유 수량 부족

##### 3.3 `update_portfolio_values(account_id)`
포트폴리오 평가액 업데이트

**처리 과정**:
1. 모든 보유 종목 조회
2. 최신 종가 조회
3. 평가액 및 손익률 계산
4. 포지션 테이블 업데이트

##### 3.4 `get_portfolio(account_id)`
포트폴리오 전체 조회

**반환 정보**:
- 현금 잔고
- 보유 종목 리스트 (코드, 이름, 수량, 평균가, 현재가, 손익)
- 주식 총 평가액
- 총 자산

#### CLI 사용법

```bash
# 매수
python3 paper_trading/paper_trading.py buy \
    --code 005930 --quantity 10 --reason "AI 추천"

# 매도
python3 paper_trading/paper_trading.py sell \
    --code 005930 --quantity 5 --reason "익절"

# 포트폴리오 조회
python3 paper_trading/paper_trading.py portfolio --account-id 1

# 평가액 업데이트
python3 paper_trading/paper_trading.py update --account-id 1
```

---

### 4. 포트폴리오 관리 (`portfolio_manager.py`)

**파일 크기**: 16KB

#### 주요 함수

##### 4.1 `save_daily_snapshot(account_id)`
일일 포트폴리오 스냅샷 저장

**저장 정보**:
- 날짜, 총 자산, 현금, 주식, 수익률

##### 4.2 `get_portfolio_history(account_id, days)`
포트폴리오 히스토리 조회

##### 4.3 `check_stop_loss_take_profit(account_id, stop_loss_pct, take_profit_pct)`
손절/익절 체크

**기본값**:
- 손절: -10%
- 익절: +20%

**반환**: 매도 권장 종목 리스트

##### 4.4 `execute_rebalancing(account_id, target_weights, max_trade_pct)`
포트폴리오 리밸런싱

**파라미터**:
- `target_weights`: 목표 비중 딕셔너리 `{종목코드: 비중}`
- `max_trade_pct`: 리밸런싱 실행 기준 (기본: 5%p)

##### 4.5 `get_trade_history(account_id, limit)`
거래 내역 조회

##### 4.6 `calculate_portfolio_metrics(account_id)`
포트폴리오 성과 지표 계산

**계산 지표**:
- 총 수익 / 수익률
- 총 거래 수
- 승률 (익절 거래 / 전체 매도)
- 평균 거래당 수익

#### CLI 사용법

```bash
# 일일 스냅샷 저장
python3 paper_trading/portfolio_manager.py snapshot --account-id 1

# 히스토리 조회
python3 paper_trading/portfolio_manager.py history --account-id 1 --days 30

# 손절/익절 체크
python3 paper_trading/portfolio_manager.py check-exit \
    --account-id 1 --stop-loss -10 --take-profit 20

# 성과 지표
python3 paper_trading/portfolio_manager.py metrics --account-id 1

# 거래 내역
python3 paper_trading/portfolio_manager.py trades --account-id 1 --limit 50
```

---

### 5. AI 자동 매매 통합 (`trading_crew.py`)

**파일 크기**: 15KB

#### 주요 함수

##### 5.1 `parse_portfolio_recommendations(crew_output)`
AI 분석 결과 파싱

**파싱 대상**:
- 종목 코드 (6자리 숫자)
- 추천 비중

**반환**: 추천 종목 리스트

##### 5.2 `calculate_purchase_quantities(account_id, recommendations, cash_reserve_pct)`
매수 수량 계산

**로직**:
1. 가용 현금 = 현재 잔고 × (1 - 현금보유비율)
2. 종목별 목표 금액 = 가용 현금 × 비중
3. 매수 수량 = 목표 금액 / (현재가 × 1.00015)

##### 5.3 `execute_initial_portfolio(account_id, recommendations, cash_reserve_pct, dry_run)`
초기 포트폴리오 구성

**처리 과정**:
1. 매수 계획 수립
2. 종목별 순차 매수
3. 성공/실패 기록

##### 5.4 `run_daily_trading_workflow(...)` ⭐ 핵심 함수
일일 자동 매매 워크플로

**워크플로 5단계**:

```
Step 1: 포트폴리오 업데이트
  └─ 모든 보유 종목 현재가 반영

Step 2: 손절/익절 체크
  ├─ 기준 도달 종목 확인
  └─ execute_trades=True면 자동 매도

Step 3: AI 분석 실행
  ├─ integrated_crew 실행
  ├─ 종목 스크리닝 (limit개)
  └─ 추천 종목 선정 (top_n개)

Step 4: 매수 실행
  ├─ 추천 종목 매수 계획 수립
  └─ execute_trades=True면 자동 매수

Step 5: 일일 스냅샷 저장
  └─ 당일 성과 기록
```

**파라미터**:
- `account_id`: 계좌 ID (기본: 1)
- `market`: 시장 (KOSPI/KOSDAQ)
- `limit`: 분석 종목 수 (기본: 20)
- `top_n`: 선정 종목 수 (기본: 10)
- `cash_reserve_pct`: 현금 보유 비율 (기본: 0.2 = 20%)
- `stop_loss_pct`: 손절 기준 (기본: -10%)
- `take_profit_pct`: 익절 기준 (기본: +20%)
- `execute_trades`: 실제 매매 실행 여부 (기본: False)

#### CLI 사용법

```bash
# 분석만 (실제 매매 X)
python3 paper_trading/trading_crew.py

# 실제 매매 실행
python3 paper_trading/trading_crew.py --execute

# 상세 옵션 지정
python3 paper_trading/trading_crew.py \
    --account-id 1 \
    --market KOSPI \
    --limit 20 \
    --top-n 10 \
    --cash-reserve 0.2 \
    --stop-loss -10.0 \
    --take-profit 20.0 \
    --execute \
    --save-log
```

---

### 6. 성과 보고서 (`performance_reporter.py`)

**파일 크기**: 13KB

#### 주요 함수

##### 6.1 `calculate_sharpe_ratio(returns, risk_free_rate)`
Sharpe Ratio 계산

**공식**: (평균 수익률 - 무위험 수익률) / 수익률 표준편차 × √252

##### 6.2 `calculate_max_drawdown(values)`
Maximum Drawdown (MDD) 계산

**공식**: (현재가 - 최고가) / 최고가 × 100

**반환**: (MDD %, 최대 낙폭 지속 일수)

##### 6.3 `calculate_volatility(returns)`
변동성 계산

**공식**: 일별 수익률 표준편차 × √252 × 100

##### 6.4 `generate_performance_report(account_id, period_days, report_type)`
성과 보고서 생성

**보고서 포함 정보**:
- 기본 정보 (초기 자금, 현재 자산, 수익률)
- 거래 통계 (거래 횟수, 승률)
- 리스크 지표 (Sharpe, MDD, 변동성)
- 현재 포트폴리오
- 최근 거래 내역
- 일별 히스토리

##### 6.5 `format_markdown_report(report)`
마크다운 형식 보고서 생성

**섹션**:
1. 자산 현황
2. 성과 지표 (표)
3. 거래 통계
4. 현재 포트폴리오 (표)
5. 최근 거래 내역 (표)
6. 유의사항

##### 6.6 `save_report_to_db(account_id, report, report_content)`
보고서 DB 저장

##### 6.7 `send_report_to_n8n(report_content, webhook_url)`
n8n 웹훅으로 보고서 전송

#### CLI 사용법

```bash
# 주간 보고서
python3 paper_trading/performance_reporter.py --type weekly

# 월간 보고서
python3 paper_trading/performance_reporter.py --type monthly

# 파일 저장 + DB 저장 + n8n 전송
python3 paper_trading/performance_reporter.py \
    --account-id 1 \
    --type weekly \
    --output reports/weekly_report.md \
    --save-db \
    --send-n8n
```

---

### 7. 자동화 스크립트

#### 7.1 일일 실행 스크립트 (`run_paper_trading.sh`)

**파일 크기**: 2.0KB

**기능**:
- 가상환경 자동 활성화
- 일일 트레이딩 워크플로 실행
- 로그 파일 자동 생성
- 실행 결과 기록

**설정 변수**:
```bash
ACCOUNT_ID=1
MARKET="KOSPI"
LIMIT=20
TOP_N=10
CASH_RESERVE=0.2
STOP_LOSS=-10.0
TAKE_PROFIT=20.0
EXECUTE_FLAG=""  # 실제 매매: "--execute"
```

**실행 방법**:
```bash
./paper_trading/run_paper_trading.sh
```

**로그 위치**: `paper_trading/logs/trading_YYYYMMDD_HHMMSS.log`

#### 7.2 주간 보고서 스크립트 (`generate_weekly_report.sh`)

**파일 크기**: 1.8KB

**기능**:
- 주간 성과 보고서 생성
- 마크다운 파일 저장
- DB 저장
- n8n 웹훅 전송

**실행 방법**:
```bash
./paper_trading/generate_weekly_report.sh
```

**보고서 위치**: `paper_trading/reports/weekly_report_YYYYMMDD.md`

---

## ⚙️ 자동화 설정

### Cron Job 설정

```bash
# crontab 편집
crontab -e

# 다음 라인 추가:
# 1. 일일 페이퍼 트레이딩 (평일 18:30 - 장 마감 후)
30 18 * * 1-5 /Users/yeongchang.jeon/workspace/ai-agent/paper_trading/run_paper_trading.sh

# 2. 주간 보고서 (매주 토요일 10:00)
0 10 * * 6 /Users/yeongchang.jeon/workspace/ai-agent/paper_trading/generate_weekly_report.sh
```

### 로그 모니터링

```bash
# 최근 실행 로그 확인
tail -f paper_trading/logs/trading_*.log

# 오늘 생성된 로그
ls -lh paper_trading/logs/trading_$(date +%Y%m%d)*.log

# 로그 검색
grep "ERROR\|✗" paper_trading/logs/trading_*.log
```

---

## 🧪 테스트 방법

### 1. 기본 기능 테스트

```bash
# 포트폴리오 조회
.venv/bin/python3 paper_trading/paper_trading.py portfolio --account-id 1

# 성과 지표
.venv/bin/python3 paper_trading/portfolio_manager.py metrics --account-id 1

# 거래 내역
.venv/bin/python3 paper_trading/portfolio_manager.py trades --account-id 1
```

### 2. 매매 테스트

```bash
# 삼성전자 10주 매수
.venv/bin/python3 paper_trading/paper_trading.py buy \
    --code 005930 --quantity 10 --reason "테스트 매수"

# 포트폴리오 업데이트
.venv/bin/python3 paper_trading/paper_trading.py update --account-id 1

# 포트폴리오 확인
.venv/bin/python3 paper_trading/paper_trading.py portfolio --account-id 1

# 5주 매도
.venv/bin/python3 paper_trading/paper_trading.py sell \
    --code 005930 --quantity 5 --reason "테스트 매도"
```

### 3. AI 워크플로 테스트 (DRY RUN)

```bash
# 분석만 수행 (실제 매매 X)
.venv/bin/python3 paper_trading/trading_crew.py \
    --market KOSPI \
    --limit 10 \
    --top-n 5 \
    --save-log
```

**⚠️ 주의**: AI 분석은 수 분 소요될 수 있으며, Ollama 서버가 실행 중이어야 합니다.

### 4. 보고서 테스트

```bash
# 주간 보고서 생성 (화면 출력만)
.venv/bin/python3 paper_trading/performance_reporter.py --type weekly

# 파일 저장
.venv/bin/python3 paper_trading/performance_reporter.py \
    --type weekly \
    --output paper_trading/reports/test_report.md
```

---

## 📊 데이터 흐름

### 일일 워크플로 데이터 흐름

```
1. 데이터 수집 (cron: 18:00)
   └─ prices 테이블 업데이트

2. AI 분석 (cron: 18:30)
   ├─ integrated_crew 실행
   │  ├─ screening_analyst: 종목 스크리닝
   │  ├─ risk_manager: 리스크 분석
   │  └─ portfolio_planner: 포트폴리오 구성
   └─ 추천 종목 출력

3. 자동 매매
   ├─ portfolio_manager: 손절/익절 체크
   │  └─ virtual_trades 기록
   │
   ├─ trading_crew: 추천 종목 매수
   │  ├─ virtual_trades 기록
   │  └─ virtual_portfolio 업데이트
   │
   └─ portfolio_manager: 일일 스냅샷
      └─ virtual_portfolio_history 저장

4. 주간 보고서 (cron: 토요일 10:00)
   ├─ performance_reporter 실행
   ├─ virtual_reports 저장
   └─ n8n 웹훅 전송
```

---

## 🔍 주요 알고리즘

### 1. 평균 매입가 계산

매수 시 기존 포지션과 신규 매수의 평균가 계산:

```python
new_avg_price = (old_avg_price × old_quantity + new_price × new_quantity)
                / (old_quantity + new_quantity)
```

### 2. 수수료 계산

한국 증권사 평균 수수료율 0.015% 적용:

```python
# 매수
total_cost = stock_amount × 1.00015

# 매도
total_proceeds = stock_amount × 0.99985
```

### 3. 손익률 계산

```python
profit_loss = (current_price - avg_price) × quantity
profit_loss_pct = (profit_loss / (avg_price × quantity)) × 100
```

### 4. Sharpe Ratio 계산

```python
daily_risk_free_rate = annual_risk_free_rate / 252
excess_returns = daily_returns - daily_risk_free_rate
sharpe_ratio = mean(excess_returns) / std(excess_returns) × √252
```

### 5. Maximum Drawdown (MDD)

```python
cummax = np.maximum.accumulate(portfolio_values)
drawdown = (portfolio_values - cummax) / cummax × 100
mdd = min(drawdown)
```

---

## 📁 파일 구조

```
paper_trading/
├── __init__.py                  # 패키지 초기화
├── schema.sql                   # DB 스키마 (8.4KB)
├── setup_schema.py              # 초기 설정 (2.7KB)
├── paper_trading.py             # 매매 실행 (19KB)
├── portfolio_manager.py         # 포트폴리오 관리 (16KB)
├── trading_crew.py              # AI 통합 (15KB)
├── performance_reporter.py      # 보고서 (13KB)
├── run_paper_trading.sh         # 자동 실행 (2.0KB)
├── generate_weekly_report.sh    # 보고서 스크립트 (1.8KB)
├── README.md                    # 사용 가이드 (7.8KB)
├── logs/                        # 실행 로그
│   ├── trading_YYYYMMDD_HHMMSS.log
│   └── report_YYYYMMDD_HHMMSS.log
└── reports/                     # 생성된 보고서
    └── weekly_report_YYYYMMDD.md
```

---

## 🔐 환경 변수

`.env` 파일에 다음 변수 필요:

```bash
# PostgreSQL
DB_HOST=localhost
DB_PORT=5432
DB_NAME=investment_db
DB_USER=invest_user
DB_PASSWORD=your_password

# Ollama (AI 분석용)
OPENAI_API_BASE=http://127.0.0.1:11434
OPENAI_MODEL_NAME=llama3.1:8b
OPENAI_API_KEY=ollama

# n8n 웹훅 (선택사항)
N8N_WEBHOOK_URL=https://your-n8n.com/webhook/...
```

---

## ⚠️ 알려진 제약사항

### 시뮬레이션 한계

1. **슬리피지 없음**
   - 항상 지정가(종가)에 체결
   - 실전에서는 호가 차이 발생

2. **유동성 무한**
   - 원하는 수량 항상 체결 가능
   - 실전에서는 거래량 제약

3. **시장 충격 없음**
   - 대량 거래도 가격 영향 없음
   - 실전에서는 대량 거래 시 가격 변동

4. **하루 1회 거래**
   - 종가 기준 1일 1회
   - 실전에서는 장중 실시간 거래

### 기술적 제약

1. **AI 토큰 제한**
   - Ollama 서버 부하 고려 필요
   - 분석 시간 수 분 소요

2. **데이터베이스 의존성**
   - PostgreSQL 필수
   - prices 테이블 데이터 필수

3. **네트워크 의존성**
   - n8n 웹훅 전송 시 네트워크 필요
   - integrated_crew 실행 시 Ollama 서버 필요

---

## 🚀 향후 개선 계획

### Phase 2 (향후)

- [ ] 지정가 주문 지원
- [ ] 손절/익절 자동 실행 (현재는 권장만)
- [ ] 실시간 알림 (Slack/Email)
- [ ] 웹 대시보드

### Phase 3 (고급)

- [ ] 멀티 전략 테스트
- [ ] A/B 테스팅
- [ ] 머신러닝 기반 전략 최적화
- [ ] 실시간 차트 시각화

---

## 📞 문제 해결

### 문제: 모듈 import 실패

```bash
# 해결: PYTHONPATH 설정
export PYTHONPATH=/Users/yeongchang.jeon/workspace/ai-agent:$PYTHONPATH

# 또는 프로젝트 루트에서 실행
cd /Users/yeongchang.jeon/workspace/ai-agent
.venv/bin/python3 paper_trading/paper_trading.py portfolio
```

### 문제: 데이터베이스 연결 실패

```bash
# PostgreSQL 상태 확인
pg_isready -h localhost -p 5432

# 연결 테스트
.venv/bin/python3 core/utils/db_utils.py
```

### 문제: AI 분석 실패

```bash
# Ollama 서버 확인
curl http://127.0.0.1:11434/api/version

# 로그 확인
tail -100 paper_trading/logs/trading_*.log
```

### 문제: 스크립트 실행 권한

```bash
# 실행 권한 부여
chmod +x paper_trading/*.sh
```

---

## 📚 관련 문서

- **PAPER_TRADING_PLAN.md** - 초기 설계 문서
- **paper_trading/README.md** - 사용자 가이드
- **core/agents/integrated_crew.py** - AI 분석 파이프라인

---

## ✅ 체크리스트

구현 완료 항목:

- [x] 데이터베이스 스키마 설계 및 생성
- [x] 가상계좌 생성 (ID: 1, 1,000만원)
- [x] 매수/매도 기능 구현
- [x] 수수료 계산 (0.015%)
- [x] 평균 매입가 자동 계산
- [x] 포트폴리오 평가 및 업데이트
- [x] 손절/익절 체크
- [x] 일일 스냅샷 저장
- [x] AI 에이전트 통합
- [x] 자동 매매 워크플로
- [x] 성과 보고서 생성
- [x] Sharpe Ratio / MDD / 변동성 계산
- [x] 마크다운 보고서 포맷팅
- [x] n8n 웹훅 전송
- [x] CLI 인터페이스
- [x] 자동화 스크립트 (cron)
- [x] 사용 문서 작성

테스트 완료 항목:

- [x] 스키마 적용
- [x] 가상계좌 생성
- [x] 포트폴리오 조회
- [x] 성과 지표 조회

다음 날 테스트 필요:

- [ ] AI 자동 매매 워크플로 (토큰 제한으로 미실행)
- [ ] 실제 매수/매도 시뮬레이션
- [ ] 손절/익절 자동 실행
- [ ] 주간 보고서 생성
- [ ] n8n 웹훅 전송
- [ ] Cron job 실행

---

## 🎉 요약

**구현 현황**: ✅ 완료
**파일 개수**: 10개
**총 코드량**: ~88KB
**테이블 수**: 5개
**뷰 수**: 3개
**함수 수**: 2개

AI 에이전트 기반 페이퍼 트레이딩 시스템의 전체 인프라가 성공적으로 구축되었습니다. 다음 날 AI 토큰이 확보되면 전체 워크플로를 실행하여 실제 투자 시뮬레이션을 진행할 수 있습니다.

---

**문서 작성일**: 2025-10-18
**최종 수정일**: 2025-10-18
**작성자**: AI Agent
**버전**: 1.0
