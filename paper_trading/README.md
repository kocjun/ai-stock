# 📊 페이퍼 트레이딩 시스템

AI 에이전트 기반 자동 투자 시뮬레이션 시스템

## 🎯 개요

실제 돈을 사용하지 않고 AI 에이전트의 투자 전략을 실전처럼 테스트하는 페이퍼 트레이딩 시스템입니다.

### 주요 기능

- ✅ 가상 계좌 관리 및 잔고 추적
- ✅ 매수/매도 시뮬레이션 (수수료 포함)
- ✅ AI 기반 종목 분석 및 자동 매매
- ✅ 손절/익절 자동 체크
- ✅ 포트폴리오 리밸런싱
- ✅ 일일/주간 성과 보고서
- ✅ 웹훅을 통한 알림 (n8n)
- ✅ **실시간 모니터링 대시보드** (NEW!)

---

## 📦 시스템 구성

### 모듈 구조

```
paper_trading/
├── schema.sql              # 데이터베이스 스키마
├── setup_schema.py         # 초기 설정 스크립트
├── paper_trading.py        # 매수/매도 실행
├── portfolio_manager.py    # 포트폴리오 관리
├── trading_crew.py         # AI 에이전트 통합
├── performance_reporter.py # 성과 보고서 생성
├── dashboard.py            # 웹 대시보드 (NEW!)
├── dashboard_data.py       # 대시보드 데이터 레이어 (NEW!)
├── run_dashboard.sh        # 대시보드 실행 스크립트 (NEW!)
├── run_paper_trading.sh    # 일일 실행 스크립트
├── generate_weekly_report.sh # 주간 보고서 스크립트
└── README.md               # 이 파일
```

### 데이터베이스 테이블

1. **virtual_accounts** - 가상 계좌
2. **virtual_trades** - 거래 내역
3. **virtual_portfolio** - 현재 포지션
4. **virtual_portfolio_history** - 일별 스냅샷
5. **virtual_reports** - 성과 보고서

---

## 🚀 시작하기

### 1. 초기 설정

```bash
# 데이터베이스 스키마 생성 및 가상계좌 생성
python3 paper_trading/setup_schema.py
```

이 명령은 다음을 수행합니다:
- 5개 테이블 생성
- 초기 자금 1,000만원으로 가상계좌 생성
- 계좌 ID는 자동으로 1번으로 생성됨

### 2. 포트폴리오 확인

```bash
# 현재 포트폴리오 조회
python3 paper_trading/paper_trading.py portfolio --account-id 1
```

### 3. 수동 매매 테스트

```bash
# 삼성전자 10주 매수
python3 paper_trading/paper_trading.py buy --code 005930 --quantity 10

# 포트폴리오 업데이트 (현재가 반영)
python3 paper_trading/paper_trading.py update

# 삼성전자 5주 매도
python3 paper_trading/paper_trading.py sell --code 005930 --quantity 5
```

---

## 🤖 AI 자동 매매

### 전체 워크플로 실행

```bash
# 분석만 수행 (실제 매매 X)
python3 paper_trading/trading_crew.py

# 실제 매매 실행
python3 paper_trading/trading_crew.py --execute

# 옵션 지정
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

### 워크플로 단계

1. **포트폴리오 업데이트** - 현재가 반영
2. **손절/익절 체크** - 기준 도달 시 자동 매도
3. **AI 분석** - integrated_crew 실행 (종목 선정)
4. **매수 실행** - 추천 종목 매수
5. **일일 스냅샷** - 성과 기록

---

## 📊 성과 보고서

### 보고서 생성

```bash
# 주간 보고서
python3 paper_trading/performance_reporter.py --type weekly

# 월간 보고서
python3 paper_trading/performance_reporter.py --type monthly

# 파일 저장 및 n8n 전송
python3 paper_trading/performance_reporter.py \
    --type weekly \
    --output reports/weekly_report.md \
    --save-db \
    --send-n8n
```

### 보고서 내용

- 자산 현황 (현금, 주식, 총 자산)
- 성과 지표 (수익률, Sharpe Ratio, MDD, 변동성)
- 거래 통계 (거래 횟수, 승률)
- 현재 포트폴리오
- 최근 거래 내역

---

## ⚙️ 자동화 설정

### Cron Job 설정

```bash
# crontab 편집
crontab -e

# 다음 라인 추가:

# 1. 일일 페이퍼 트레이딩 (평일 오전 10시 - 시장 개장 후)
0 10 * * 1-5 /Users/yeongchang.jeon/workspace/ai-agent/paper_trading/run_paper_trading.sh

# 2. 주간 레드팀 검증 (매주 토요일 오전 6시)
0 6 * * 6 /Users/yeongchang.jeon/workspace/ai-agent/paper_trading/run_redteam_validation.sh

# 3. 주간 보고서 (매주 토요일 오전 7시)
0 7 * * 6 /Users/yeongchang.jeon/workspace/ai-agent/paper_trading/generate_weekly_report.sh
```

### 로그 확인

```bash
# 최근 실행 로그
tail -100 paper_trading/logs/trading_*.log

# 최근 보고서
cat paper_trading/reports/weekly_report_*.md
```

---

## 💡 전략 설정

### 기본 전략 (AI 종합 분석)

현재 설정된 기본 전략:

- **현금 보유**: 20% (cash_reserve_pct=0.2)
- **투자 대상**: KOSPI 상위 20개 분석 → 10개 선정
- **손절 기준**: -10%
- **익절 기준**: +20%
- **리밸런싱**: 비중 5%p 이상 이탈 시

### 전략 수정

`run_paper_trading.sh` 파일의 다음 변수를 수정:

```bash
MARKET="KOSPI"          # 시장 (KOSPI/KOSDAQ)
LIMIT=20                # 분석 종목 수
TOP_N=10                # 선정 종목 수
CASH_RESERVE=0.2        # 현금 보유 비율 (0.2 = 20%)
STOP_LOSS=-10.0         # 손절 기준 (%)
TAKE_PROFIT=20.0        # 익절 기준 (%)
EXECUTE_FLAG=""         # 실제 매매: "--execute"
```

---

## 🧪 테스트

### 1. 기본 기능 테스트

```bash
# 포트폴리오 조회
python3 paper_trading/paper_trading.py portfolio

# 포트폴리오 관리
python3 paper_trading/portfolio_manager.py snapshot
python3 paper_trading/portfolio_manager.py metrics
python3 paper_trading/portfolio_manager.py check-exit
```

### 2. 보고서 테스트

```bash
# 주간 보고서 생성 (DB 저장, n8n 전송)
python3 paper_trading/performance_reporter.py \
    --type weekly \
    --save-db \
    --send-n8n
```

### 3. 전체 워크플로 테스트 (DRY RUN)

```bash
# 실제 매매 없이 분석만 수행
./paper_trading/run_paper_trading.sh
```

---

## 📈 모니터링

### 🖥️ 웹 대시보드 (추천)

실시간 모니터링을 위한 웹 기반 대시보드를 제공합니다.

```bash
# 대시보드 실행
./paper_trading/run_dashboard.sh

# 또는 직접 실행
cd paper_trading
python3 dashboard.py
```

**접속 주소**: http://localhost:8050

#### 대시보드 주요 기능

1. **포트폴리오 현황**
   - 총 자산, 현금 잔고, 주식 평가액, 수익률
   - 보유 종목 테이블 (종목명, 수량, 평단가, 현재가, 손익률)
   - 포트폴리오 비중 파이 차트

2. **성과 분석**
   - 핵심 지표 (총 거래, 승률, Sharpe Ratio, MDD)
   - 자산 추이 라인 차트 (최근 30일)
   - 일별 수익률 바 차트

3. **거래 내역**
   - 최근 거래 내역 테이블
   - 필터링 (전체/매수/매도)
   - 조회 건수 조정 가능

4. **실시간 업데이트**
   - 자동 새로고침 (30초마다)
   - 수동 업데이트 버튼
   - 마지막 업데이트 시간 표시

#### 스크린샷 예시

대시보드는 Bootstrap 테마를 사용한 깔끔하고 전문적인 UI를 제공하며,
모든 차트는 인터랙티브하게 확대/축소 및 호버 정보를 지원합니다.

### CLI 명령어

CLI를 선호하는 경우 다음 명령어를 사용할 수 있습니다:

```bash
# 계좌 요약
python3 paper_trading/portfolio_manager.py metrics --account-id 1

# 거래 내역
python3 paper_trading/portfolio_manager.py trades --account-id 1 --limit 20

# 포트폴리오 히스토리
python3 paper_trading/portfolio_manager.py history --account-id 1 --days 30

# 손절/익절 체크
python3 paper_trading/portfolio_manager.py check-exit --account-id 1
```

### 데이터베이스 조회

```sql
-- 계좌 요약
SELECT * FROM v_account_summary WHERE account_id = 1;

-- 포지션 상세
SELECT * FROM v_position_details WHERE account_id = 1;

-- 최근 거래
SELECT * FROM v_trade_details WHERE account_id = 1 ORDER BY trade_date DESC LIMIT 10;

-- 성과 추이
SELECT snapshot_date, total_value, return_pct
FROM virtual_portfolio_history
WHERE account_id = 1
ORDER BY snapshot_date DESC
LIMIT 30;
```

---

## ⚠️ 주의사항

### 시뮬레이션 한계

1. **슬리피지 없음** - 항상 지정가에 체결
2. **유동성 무한** - 원하는 수량 항상 체결 가능
3. **시장 충격 없음** - 대량 거래도 가격 영향 없음
4. **실시간 아님** - 하루 1회 종가 기준 거래

### 실전 적용 시

- 소액으로 시작하여 전략 검증
- 슬리피지 및 유동성 고려
- 급격한 시장 변동에 주의
- 손절 기준 엄격히 준수

### 면책 조항

```
본 시스템은 교육 및 연구 목적의 시뮬레이션입니다.
- 실제 투자 권유가 아닙니다
- 과거 성과가 미래 수익을 보장하지 않습니다
- 모든 투자 결정은 본인 책임입니다
```

---

## 🔧 트러블슈팅

### 문제: 스키마 적용 실패

```bash
# PostgreSQL 연결 확인
python3 core/utils/db_utils.py

# 수동으로 스키마 적용
psql -h localhost -U invest_user -d investment_db -f paper_trading/schema.sql
```

### 문제: AI 분석 실패

```bash
# Ollama 서버 확인
curl http://127.0.0.1:11434/api/version

# 환경 변수 확인
cat .env | grep OPENAI
```

### 문제: n8n 전송 실패

```bash
# 웹훅 URL 확인
echo $N8N_WEBHOOK_URL

# .env 파일에 추가
echo "N8N_WEBHOOK_URL=https://your-n8n-instance.com/webhook/..." >> .env
```

### 문제: 대시보드 실행 실패

```bash
# Dash 패키지 설치
pip install dash dash-bootstrap-components

# 의존성 전체 재설치
pip install -r requirements.txt

# 포트 8050이 이미 사용 중인 경우
# dashboard.py 파일의 마지막 줄에서 포트 변경
# app.run_server(debug=True, host='0.0.0.0', port=8051)
```

### 문제: 대시보드에 데이터가 표시되지 않음

```bash
# 1. 포트폴리오 업데이트 실행
python3 paper_trading/paper_trading.py update --account-id 1

# 2. 일일 스냅샷이 있는지 확인
python3 paper_trading/portfolio_manager.py history --account-id 1 --days 7

# 3. 스냅샷이 없다면 수동 생성
python3 paper_trading/portfolio_manager.py snapshot --account-id 1
```

---

## 📚 추가 문서

- [PAPER_TRADING_PLAN.md](../docs/PAPER_TRADING_PLAN.md) - 상세 설계 문서
- [integrated_crew.py](../core/agents/integrated_crew.py) - AI 분석 파이프라인

---

**작성일**: 2025-10-18
**최종 수정**: 2025-10-22
**버전**: 1.1 (웹 대시보드 추가)
