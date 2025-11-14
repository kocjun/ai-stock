# 📊 페이퍼 트레이딩 시스템 설계

## 🎯 목표

실제 돈을 사용하지 않고 AI 에이전트의 투자 전략을 실전처럼 테스트하는 시스템

---

## 🏗️ 시스템 아키텍처

```
[데이터 수집] → [AI 분석] → [투자 결정] → [가상 거래] → [포트폴리오 관리] → [보고서]
     ↓              ↓            ↓             ↓              ↓               ↓
  prices    screening_crew   매수/매도    virtual_trades  포지션 추적      성과 분석
```

---

## 💾 데이터베이스 스키마

### 1. virtual_accounts (가상 계좌)
```sql
CREATE TABLE virtual_accounts (
    account_id SERIAL PRIMARY KEY,
    account_name VARCHAR(100) NOT NULL,
    initial_balance DECIMAL(15,2) NOT NULL,
    current_balance DECIMAL(15,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'active'
);
```

### 2. virtual_trades (가상 거래)
```sql
CREATE TABLE virtual_trades (
    trade_id SERIAL PRIMARY KEY,
    account_id INTEGER REFERENCES virtual_accounts(account_id),
    code VARCHAR(10) NOT NULL,
    trade_type VARCHAR(10) NOT NULL,  -- 'buy' or 'sell'
    quantity INTEGER NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    total_amount DECIMAL(15,2) NOT NULL,
    trade_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reason TEXT,  -- 매매 사유
    FOREIGN KEY (code) REFERENCES stocks(code)
);
```

### 3. virtual_portfolio (현재 포지션)
```sql
CREATE TABLE virtual_portfolio (
    position_id SERIAL PRIMARY KEY,
    account_id INTEGER REFERENCES virtual_accounts(account_id),
    code VARCHAR(10) NOT NULL,
    quantity INTEGER NOT NULL,
    avg_price DECIMAL(10,2) NOT NULL,  -- 평균 매입가
    current_price DECIMAL(10,2),
    current_value DECIMAL(15,2),
    profit_loss DECIMAL(15,2),
    profit_loss_pct DECIMAL(10,4),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (code) REFERENCES stocks(code),
    UNIQUE(account_id, code)
);
```

### 4. virtual_reports (보고서)
```sql
CREATE TABLE virtual_reports (
    report_id SERIAL PRIMARY KEY,
    account_id INTEGER REFERENCES virtual_accounts(account_id),
    report_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_value DECIMAL(15,2),  -- 총 자산
    cash_balance DECIMAL(15,2),  -- 현금
    stock_value DECIMAL(15,2),  -- 주식 평가액
    total_return DECIMAL(15,2),  -- 총 수익
    return_pct DECIMAL(10,4),  -- 수익률
    num_positions INTEGER,  -- 보유 종목 수
    num_trades INTEGER,  -- 총 거래 횟수
    report_content TEXT  -- 보고서 내용
);
```

---

## 🔄 워크플로

### 1️⃣ 초기화 (한 번만)
```python
# 가상 계좌 생성
account = create_virtual_account(
    name="AI 투자 시뮬레이션 #1",
    initial_balance=10_000_000  # 1천만원
)
```

### 2️⃣ 일간 사이클 (매일 실행)
```python
# Step 1: 데이터 수집 (이미 cron으로 실행 중)
# → prices 테이블 업데이트

# Step 2: AI 분석 및 투자 결정
recommendations = run_integrated_analysis()
# → screening_crew + risk_manager + portfolio_planner

# Step 3: 매매 결정 및 실행
for rec in recommendations:
    if rec['action'] == 'buy':
        execute_buy(account, rec['code'], rec['quantity'])
    elif rec['action'] == 'sell':
        execute_sell(account, rec['code'], rec['quantity'])

# Step 4: 포트폴리오 업데이트
update_portfolio_values(account)
```

### 3️⃣ 주간 보고서 (매주)
```python
# 성과 분석
report = generate_performance_report(account)
# → total_return, return_pct, sharpe_ratio, mdd 등

# 보고서 저장 및 전송
save_report(report)
send_notification(report)  # n8n webhook
```

---

## 🎯 구현 모듈

### 1. virtual_account.py
- 계좌 생성/조회
- 잔고 관리
- 거래 실행
- 포지션 추적

### 2. paper_trading.py
- 매수/매도 로직
- 시장가/지정가 시뮬레이션
- 수수료 계산 (0.015% 매수/매도)
- 거래 유효성 검증

### 3. trading_crew.py
- AI 에이전트 통합
- 매매 결정 로직
- 리스크 관리
- 포트폴리오 리밸런싱

### 4. performance_reporter.py
- 성과 지표 계산
- 보고서 생성 (Markdown)
- 시각화 (차트)
- 알림 전송

---

## 📅 실행 스케줄

### cron job 설정

```bash
# 1. 데이터 수집 (이미 설정됨)
0 18 * * * run_daily_collection.sh

# 2. AI 분석 및 매매 결정 (매일 장 마감 후)
30 18 * * 1-5 run_paper_trading.sh

# 3. 주간 보고서 (매주 토요일)
0 10 * * 6 generate_weekly_report.sh
```

---

## 💡 핵심 기능

### 매수 로직
```python
def execute_buy(account, code, quantity):
    """
    1. 현재가 조회
    2. 필요 금액 계산 (수수료 포함)
    3. 잔고 확인
    4. 거래 실행
    5. 포트폴리오 업데이트
    """
    current_price = get_latest_price(code)
    total_cost = current_price * quantity * 1.00015  # 수수료 0.015%

    if account.cash_balance >= total_cost:
        # 거래 실행
        trade = record_trade(account, code, 'buy', quantity, current_price)
        update_balance(account, -total_cost)
        update_position(account, code, quantity, current_price)
        return trade
    else:
        raise InsufficientFundsError()
```

### 매도 로직
```python
def execute_sell(account, code, quantity):
    """
    1. 보유량 확인
    2. 현재가 조회
    3. 매도 금액 계산 (수수료 차감)
    4. 거래 실행
    5. 포트폴리오 업데이트
    """
    position = get_position(account, code)

    if position.quantity >= quantity:
        current_price = get_latest_price(code)
        total_proceeds = current_price * quantity * 0.99985  # 수수료 0.015%

        trade = record_trade(account, code, 'sell', quantity, current_price)
        update_balance(account, +total_proceeds)
        update_position(account, code, -quantity, current_price)
        return trade
    else:
        raise InsufficientSharesError()
```

### 포트폴리오 업데이트
```python
def update_portfolio_values(account):
    """
    매일 종가 기준으로 포트폴리오 평가
    """
    positions = get_all_positions(account)

    for pos in positions:
        current_price = get_latest_price(pos.code)
        current_value = current_price * pos.quantity
        profit_loss = current_value - (pos.avg_price * pos.quantity)
        profit_loss_pct = (profit_loss / (pos.avg_price * pos.quantity)) * 100

        update_position_values(pos, current_price, current_value, profit_loss, profit_loss_pct)
```

---

## 📊 투자 전략

### 전략 1: AI 종합 분석 (기본)
```python
# 1. Screening: 상위 20개 종목 선정
# 2. Risk Analysis: 리스크 평가
# 3. Portfolio Optimization: 최적 비중 계산
# 4. 매수: 현금의 80% 투자 (20% 현금 보유)
# 5. 리밸런싱: 주 1회 (비중 5%p 이상 이탈 시)
# 6. 손절/익절: 손절 -10%, 익절 +20%
```

### 전략 2: 보수적 전략
```python
# - 현금 50% 유지
# - 대형주 위주 (시총 상위 50개)
# - 분산 투자 (최소 10개 종목)
# - 손절 -5%, 익절 +15%
```

### 전략 3: 공격적 전략
```python
# - 현금 10% 유지
# - 성장주 위주 (팩터 스코어 상위)
# - 집중 투자 (5-7개 종목)
# - 손절 -15%, 익절 +30%
```

---

## 🎮 사용 예시

### 초기 설정
```bash
# 1. 데이터베이스 스키마 생성
python setup_paper_trading.py

# 2. 가상 계좌 생성
python -c "
from virtual_account import create_virtual_account
account = create_virtual_account(
    name='AI 투자 시뮬레이션',
    initial_balance=10_000_000
)
print(f'계좌 생성: {account.account_id}')
"

# 3. 자동화 설정
./setup_paper_trading_cron.sh
```

### 수동 실행
```bash
# 전체 워크플로 실행
python trading_crew.py --account-id 1

# 특정 종목 매수
python paper_trading.py buy 005930 10

# 포트폴리오 확인
python paper_trading.py portfolio

# 보고서 생성
python performance_reporter.py --account-id 1
```

---

## 📈 성과 지표

### 계산 지표
1. **총 수익률**: (현재 총 자산 - 초기 자금) / 초기 자금 × 100
2. **연평균 수익률**: CAGR
3. **Sharpe Ratio**: (수익률 - 무위험 수익률) / 변동성
4. **MDD (Maximum Drawdown)**: 최대 낙폭
5. **승률**: 익절 거래 수 / 총 거래 수
6. **평균 수익**: 총 수익 / 거래 횟수
7. **보유 기간**: 평균 포지션 보유 일수
8. **회전율**: 연간 거래 금액 / 평균 자산

### 벤치마크 비교
- KOSPI 지수 대비 성과
- 동일 기간 Buy & Hold 대비

---

## ⚠️ 주의사항

### 면책 조항
```
본 시스템은 교육 및 연구 목적의 시뮬레이션입니다.
- 실제 투자 권유가 아닙니다
- 과거 성과가 미래 수익을 보장하지 않습니다
- 실제 매매 시 슬리피지, 유동성 문제 등이 발생할 수 있습니다
- 모든 투자 결정은 본인 책임입니다
```

### 시뮬레이션 제약
1. **슬리피지 없음**: 항상 종가에 체결
2. **유동성 무한**: 원하는 수량 항상 체결
3. **부분 체결 없음**: 전량 체결 또는 미체결
4. **시장 충격 없음**: 대량 거래 시에도 가격 영향 없음

---

## 🔮 향후 개선

### Phase 1 (현재)
- ✅ 기본 페이퍼 트레이딩
- ✅ 시장가 매매
- ✅ 일간/주간 보고서

### Phase 2 (향후)
- 지정가 주문
- 손절/익절 자동 실행
- 실시간 알림 (Slack/Email)
- 웹 대시보드

### Phase 3 (고급)
- 멀티 전략 테스트
- A/B 테스팅
- 머신러닝 기반 전략 최적화
- 실시간 차트 시각화

---

**작성일**: 2025-10-18
**버전**: 1.0
