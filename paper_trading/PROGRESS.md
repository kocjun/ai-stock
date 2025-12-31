# 투자 룰 기반 페이퍼 트레이딩 시스템 개발 진행 상황

**작업 시작일**: 2025-12-31
**최종 업데이트**: 2025-12-31 22:40 (Phase 1.3 부분 완료 - 6개 룰 추가)

---

## ✅ 완료된 작업 (Phase 1 - 90% 완료)

### 1. 프로젝트 환경 구축
- ✅ 프로젝트 현재 상태 파악
- ✅ Python 가상환경 재생성 (Python 3.11.2)
- ✅ 필요 패키지 설치 (CrewAI, pandas, psycopg2 등)
- ✅ 데이터베이스 연결 확인 (PostgreSQL, 198 종목, 5,767 가격 데이터)

### 2. 시스템 탐색 및 분석
- ✅ 페이퍼 트레이딩 시스템 구조 분석 완료
- ✅ 기존 투자 전략 구현 방식 파악
- ✅ 데이터 수집 시스템 탐색 (FinanceDataReader 사용 중)

### 3. 구현 계획 수립
- ✅ 5단계 Phase 상세 계획 작성 (`/root/.claude/plans/rippling-launching-token.md`)
- ✅ Phase별 구현 순서 및 우선순위 정의
- ✅ 핵심 파일 목록 (신규 11개, 수정 5개) 정리

### 4. Phase 1.1: DB 스키마 생성 ✅
**파일**: `/workspace/ai-stock/paper_trading/investment_rules_schema.sql`

- ✅ 5개 테이블 생성:
  - `investment_rules`: 투자 룰 정의
  - `rule_executions`: 룰 실행 히스토리
  - `dca_schedules`: DCA 월간 스케줄
  - `rebalancing_history`: 리밸런싱 기록
  - `realtime_price_cache`: 실시간 가격 캐시

- ✅ 3개 뷰 생성:
  - `v_active_rules`: 활성화된 룰 목록
  - `v_pending_dca_schedules`: 실행 대기 DCA 스케줄
  - `v_rule_performance`: 룰별 성과 통계

- ✅ 기존 테이블 확장:
  - `virtual_accounts`: `rule_set_id`, `auto_trading_enabled` 컬럼 추가
  - `virtual_trades`: `rule_id`, `execution_id` 컬럼 추가

**스키마 적용 방법**:
```bash
.venv/bin/python paper_trading/apply_schema.py
```

### 5. Phase 1.2: 룰 파서 개발 ✅
**파일**: `/workspace/ai-stock/paper_trading/rule_parser.py`

- ✅ Pydantic 모델 정의 (InvestmentRuleModel, InvestmentCondition, InvestmentAction)
- ✅ 정규식 기반 파싱 구현:
  - 종목명, 금액, 변동률, 주차, 비율 추출
  - 룰 타입 자동 추정 (DCA, SIGNAL, TAKE_PROFIT, STOP_LOSS)
  - 자산 카테고리 추정 (CORE, SATELLITE, DEFENSE)

- ✅ 검증 로직 (Pydantic)

**테스트 방법**:
```bash
.venv/bin/python paper_trading/rule_parser.py
```

### 6. Phase 1.3: 룰 매니저 CLI ✅
**파일**: `/workspace/ai-stock/paper_trading/rule_manager.py`

- ✅ 룰 CRUD 기능:
  - `add`: 텍스트로 룰 추가
  - `list`: 룰 목록 조회
  - `show`: 특정 룰 상세 조회
  - `toggle`: 룰 활성화/비활성화
  - `delete`: 룰 삭제

- ✅ DB 연동 완료
- ✅ 투자 룰 6개 추가 성공:
  - 코어 자산 3개: KODEX 200, TIGER S&P500, KODEX 고배당
  - 위성 자산 3개: KODEX 코스닥150 (하락 매수 2개, 익절 1개)

**사용 방법**:
```bash
# 룰 추가
.venv/bin/python paper_trading/rule_manager.py add "KODEX 200: 월 70만원 DCA"

# 룰 목록 조회
.venv/bin/python paper_trading/rule_manager.py list

# 특정 룰 조회
.venv/bin/python paper_trading/rule_manager.py show 1

# 룰 활성화/비활성화
.venv/bin/python paper_trading/rule_manager.py toggle 1

# 룰 삭제
.venv/bin/python paper_trading/rule_manager.py delete 1
```

### 7. 투자 룰 파일 준비 ✅
**파일**: `/workspace/ai-stock/paper_trading/my_investment_rules.txt`

- ✅ 맹달집사님 투자 룰 11개 정리:
  - 코어 자산 DCA 3개 (KODEX 200, TIGER S&P500, KODEX 고배당)
  - 위성 자산 신호형 7개 (코스닥150, 반도체TOP10, 한화에어로)
  - 방어 자산 대기금 1개 (TIGER 단기채)

---

## 🚧 진행 중 작업

### Phase 1.3: 룰 매니저 CLI - 테스트 및 검증
- ✅ 투자 룰 6개 추가 완료 (코어 3개, 위성 3개)
- ⏳ 나머지 5개 투자 룰 추가 예정 (내일 진행):
  - TIGER 반도체TOP10: 3개 (하락 매수 2개, 익절 1개)
  - 한화에어로스페이스: 1개 (익절)
  - TIGER 단기채권액티브: 1개 (대기금)
- ⏳ 룰 파서 LLM 통합 개선 (현재는 정규식만 사용)

---

## 📋 남은 작업 (다음 작업 시 진행)

### Phase 2: DCA 자동 실행 시스템
1. **Phase 2.1: DCA 스케줄러** (`schedulers/dca_scheduler.py`)
   - 매월 1일 월간 스케줄 자동 생성
   - 주차 계산 (1주차, 2-3주차, 마지막주)
   - 비율 배분 (50%, 30%, 20%)

2. **Phase 2.2: 룰 엔진** (`rule_engine.py`)
   - DCA 룰 실행 로직
   - 조건 평가 및 액션 트리거
   - 거래 실행 연동 (`paper_trading.py`)

3. **Phase 2.3: 포트폴리오 매니저 개선** (`portfolio_manager.py`)
   - `execute_dca_purchase()` 함수 추가
   - 대기금 관리 로직

### Phase 3: 실시간 모니터링 시스템
1. **Phase 3.1: 한국투자증권 API 클라이언트** (`realtime/kis_api_client.py`)
   - python-kis 라이브러리 통합
   - WebSocket 연결 관리
   - 실시간 시세 수신

2. **Phase 3.2: 실시간 모니터** (`realtime/realtime_monitor.py`)
   - 30초/1분 단위 변동률 계산
   - 신호형 룰 조건 감지
   - 자동 매수/매도 트리거

3. **Phase 3.3: 가격 캐시 및 업데이터 개선**
   - `price_cache.py`: 인메모리 캐시
   - `price_updater.py`: KIS API 통합

### Phase 4: 비중 관리 및 리밸런싱
- 비중 계산 로직
- 리밸런싱 스케줄러
- 목표 밴드 모니터링

### Phase 5: 대시보드
- 투자 룰 페이지 추가
- 룰별 실행 히스토리 차트
- 성과 지표 시각화

---

## 🔧 환경 설정 (아직 필요)

### requirements.txt 추가 필요
```txt
python-kis>=1.0.0  # 한국투자증권 API
redis>=5.0.0  # 선택적 (실시간 캐시)
pydantic>=2.0.0  # 이미 설치됨
```

### .env 추가 필요
```bash
# KIS API 설정 (Phase 3에서 필요)
KIS_APP_KEY=your_app_key
KIS_APP_SECRET=your_app_secret
KIS_ACCOUNT_NUMBER=your_account_number
KIS_REAL_MODE=false  # true=실전, false=모의

# 실시간 모니터링 설정
REALTIME_MONITORING_ENABLED=true
REALTIME_UPDATE_INTERVAL=30  # 초
```

---

## 📝 다음 작업 시 시작 방법

### 1. 가상환경 활성화
```bash
cd /workspace/ai-stock
source .venv/bin/activate  # 또는 .venv/bin/python으로 직접 실행
```

### 2. 투자 룰 일괄 추가 (추천)
```bash
# 11개 투자 룰 추가
.venv/bin/python paper_trading/rule_manager.py add "KODEX 200: 월 70만원 정기 매수 (1주차 50%, 2-3주차 30%, 마지막주 20%)"
.venv/bin/python paper_trading/rule_manager.py add "TIGER 미국 S&P500: 월 60만원 정기 매수 (1주차 50%, 2-3주차 30%, 마지막주 20%)"
.venv/bin/python paper_trading/rule_manager.py add "KODEX 고배당: 월 30만원 정기 매수 (1주차 50%, 2-3주차 30%, 마지막주 20%)"
# ... (나머지 룰들)

# 또는 룰 목록 확인
.venv/bin/python paper_trading/rule_manager.py list
```

### 3. Phase 2 시작: DCA 스케줄러 개발
```bash
# schedulers 디렉터리 생성
mkdir -p paper_trading/schedulers

# DCA 스케줄러 개발 시작
# 파일: paper_trading/schedulers/dca_scheduler.py
```

---

## 🎯 핵심 성과

1. **투자 룰 저장 인프라 완성** (DB 스키마, 테이블, 뷰)
2. **투자 룰 파서 완성** (텍스트 → 구조화 데이터 변환)
3. **투자 룰 관리 CLI 완성** (추가, 조회, 수정, 삭제)
4. **투자 룰 6개 추가 성공** (코어 3개, 위성 3개) - 전체 11개 중 55% 완료

---

## 🔗 관련 파일

- **계획서**: `/root/.claude/plans/rippling-launching-token.md`
- **DB 스키마**: `/workspace/ai-stock/paper_trading/investment_rules_schema.sql`
- **룰 파서**: `/workspace/ai-stock/paper_trading/rule_parser.py`
- **룰 매니저**: `/workspace/ai-stock/paper_trading/rule_manager.py`
- **투자 룰 파일**: `/workspace/ai-stock/paper_trading/my_investment_rules.txt`
- **스키마 적용 스크립트**: `/workspace/ai-stock/paper_trading/apply_schema.py`

---

## 💡 참고사항

### 현재 제한사항
- LLM 파싱은 아직 비활성화 (정규식만 사용)
- 실시간 데이터 수집 미구현 (Phase 3에서 진행 예정)
- DCA 자동 실행 미구현 (Phase 2에서 진행 예정)

### 강점
- 정규식 파싱만으로도 대부분의 투자 룰 파싱 가능
- DB 스키마가 확장 가능하게 설계됨 (JSON 필드 활용)
- CLI 도구로 쉬운 룰 관리 가능

---

**다음 작업 우선순위**:
1. 🚀 Phase 1.3 완료 (나머지 5개 투자 룰 추가)
2. 🚀 Phase 2.1 시작 (DCA 스케줄러)
3. 🚀 Phase 2.2 (룰 엔진)
