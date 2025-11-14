# 워크플로우 테스트 가이드

**작성일**: 2025-10-20
**목적**: n8n 워크플로우 및 Python 에이전트 테스트 방법

---

## ✅ 테스트 완료 항목

- [x] 프로젝트 구조 모듈화
- [x] Import 경로 수정
- [x] 가상환경 및 의존성 설치
- [x] n8n 워크플로우 경로 업데이트
- [x] 에이전트 실행 테스트

---

## 🧪 테스트 방법

### 방법 1: Python 에이전트 직접 실행 (추천)

n8n 없이 에이전트를 직접 실행하여 빠르게 테스트

```bash
cd /Users/yeongchang.jeon/workspace/ai-agent
source .venv/bin/activate

# 1. 데이터 수집 (Data Curator)
python core/agents/investment_crew.py

# 2. 종목 스크리닝 (Screening Analyst)
python core/agents/screening_crew.py

# 3. 리스크 분석 (Risk Manager)
python core/agents/risk_crew.py

# 4. 포트폴리오 최적화 (Portfolio Planner)
python core/agents/portfolio_crew.py

# 5. 전체 통합 워크플로우
python core/agents/integrated_crew.py
```

---

### 방법 2: n8n 워크플로우 실행

#### A. 웹 인터페이스에서 수동 실행

1. 브라우저에서 n8n 접속
   ```bash
   open http://localhost:5678
   ```

2. 워크플로우 선택

3. "Execute Workflow" 버튼 클릭

#### B. Webhook으로 트리거

```bash
# 데이터 수집 워크플로우 트리거
curl -X POST http://localhost:5678/webhook/crew-webhook \
  -H "Content-Type: application/json" \
  -d '{
    "market": "KOSPI",
    "limit": 50,
    "days": 30
  }'
```

---

## 📊 각 워크플로우 설명

### 1. Data Curator (데이터 수집)

**파일**: `core/agents/investment_crew.py`
**n8n 워크플로우**: `data_collection_workflow.json`

**기능**:
- 코스피/코스닥 종목 데이터 수집
- 가격 데이터 수집 (일봉)
- 데이터 품질 검증
- PostgreSQL 저장

**실행 시간**: 약 5-10분 (종목 50개 기준)

**출력**:
```
✓ 수집된 종목 수: 50개
✓ 수집된 가격 데이터: 1,500 rows
✓ 데이터 커버리지: 100%
```

**n8n 스케줄**: 매일 18:00 (장 마감 후)

---

### 2. Screening Analyst (종목 스크리닝)

**파일**: `core/agents/screening_crew.py`
**n8n 워크플로우**: (Phase 4에서 추가 예정)

**기능**:
- 재무 지표 계산 (PER, PBR, ROE 등)
- 팩터 스코어링 (밸류, 성장, 수익성, 모멘텀, 안정성)
- 기술적 지표 분석 (RSI, MACD, 볼린저 밴드)
- 투자 유망 종목 선정

**실행 시간**: 약 3-5분

**출력**:
```
✓ 상위 20개 종목 리스트
✓ 각 종목의 팩터 점수
✓ 매수/관망/매도 시그널
```

---

### 3. Risk Manager (리스크 분석)

**파일**: `core/agents/risk_crew.py`
**n8n 워크플로우**: (Phase 4에서 추가 예정)

**기능**:
- 개별 종목 리스크 분석
- 포트폴리오 리스크 측정
- 변동성, MDD, VaR 계산
- Sharpe Ratio, Sortino Ratio
- 리스크 경고 및 제안

**실행 시간**: 약 2-3분

**출력**:
```
✓ 리스크 점수 (0-10)
✓ 경고 사항
✓ 리스크 관리 제안
```

---

### 4. Portfolio Planner (포트폴리오 최적화)

**파일**: `core/agents/portfolio_crew.py`
**n8n 워크플로우**: (Phase 4에서 추가 예정)

**기능**:
- 3가지 포트폴리오 전략 비교
  - 동일가중 (Equal Weight)
  - 시가총액가중 (Market Cap Weight)
  - 리스크 패리티 (Risk Parity)
- 섹터 분산도 분석
- 리밸런싱 제안
- 성과 시뮬레이션

**실행 시간**: 약 3-5분

**출력**:
```
✓ 추천 포트폴리오 구성
✓ 각 전략의 예상 수익/리스크
✓ 리밸런싱 시점 및 방법
```

---

### 5. Integrated Workflow (통합 워크플로우)

**파일**: `core/agents/integrated_crew.py`
**n8n 워크플로우**: `weekly_analysis_workflow.json`

**기능**:
- 전체 분석 프로세스 자동 실행
- Data Curator → Screening → Risk → Portfolio 순차 실행
- 종합 투자 리포트 생성

**실행 시간**: 약 15-25분

**출력**:
```
✓ 종합 투자 분석 리포트
✓ 추천 종목 및 포트폴리오
✓ 리스크 분석 및 경고
```

**n8n 스케줄**: 매주 토요일 09:00

---

## 🔍 결과 확인 방법

### 1. PostgreSQL 데이터 확인

```bash
# PostgreSQL 접속
docker exec -it investment_postgres psql -U invest_user -d investment_db

# 종목 데이터 확인
SELECT COUNT(*) as total_stocks FROM stocks;
SELECT * FROM stocks LIMIT 10;

# 가격 데이터 확인
SELECT COUNT(*) as total_prices FROM prices;
SELECT * FROM prices ORDER BY date DESC LIMIT 10;

# 로그 확인
SELECT * FROM data_collection_logs ORDER BY created_at DESC LIMIT 5;
```

### 2. n8n 실행 이력 확인

1. n8n 대시보드 접속: http://localhost:5678
2. 왼쪽 메뉴 "Executions" 클릭
3. 최근 실행 이력 및 결과 확인

### 3. 로그 파일 확인

```bash
# 실행 로그 (있는 경우)
tail -f logs/*.log

# n8n 로그
docker logs n8n --tail 100
```

---

## 🐛 문제 해결

### 문제 1: ModuleNotFoundError

**증상**:
```
ModuleNotFoundError: No module named 'core.tools'
```

**해결**:
```bash
# 프로젝트 루트에서 실행해야 함
cd /Users/yeongchang.jeon/workspace/ai-agent
source .venv/bin/activate
python core/agents/investment_crew.py
```

### 문제 2: Ollama 연결 실패

**증상**:
```
ERROR: Failed to connect to Ollama server
```

**해결**:
```bash
# Ollama 서버 확인
curl http://localhost:11434/api/tags

# Ollama 실행
ollama serve

# 모델 확인
ollama list
```

### 문제 3: PostgreSQL 연결 실패

**증상**:
```
psycopg2.OperationalError: could not connect to server
```

**해결**:
```bash
# Docker 컨테이너 확인
docker ps | grep postgres

# 컨테이너 재시작
docker-compose restart postgres

# 연결 테스트
docker exec -it investment_postgres psql -U invest_user -d investment_db
```

### 문제 4: n8n 워크플로우 실행 실패

**증상**: 워크플로우가 실행되지 않음

**해결**:
1. 워크플로우가 활성화(Active) 상태인지 확인
2. 경로가 올바른지 확인 (`core/agents/...`)
3. 실행 권한 확인
4. n8n Executions 메뉴에서 에러 로그 확인

---

## ✅ 테스트 체크리스트

### 사전 준비
- [ ] Docker 컨테이너 실행 (`docker ps`)
- [ ] Ollama 서버 실행 (`ollama serve`)
- [ ] 가상환경 활성화 (`source .venv/bin/activate`)

### 데이터 수집 워크플로우
- [ ] `investment_crew.py` 실행 성공
- [ ] 종목 데이터 DB 저장 확인
- [ ] 가격 데이터 DB 저장 확인
- [ ] 로그 기록 확인

### 분석 워크플로우
- [ ] `screening_crew.py` 실행 성공
- [ ] 종목 스크리닝 결과 확인
- [ ] 팩터 점수 계산 확인

### 리스크 & 포트폴리오
- [ ] `risk_crew.py` 실행 성공
- [ ] `portfolio_crew.py` 실행 성공
- [ ] 리스크 지표 계산 확인
- [ ] 포트폴리오 최적화 결과 확인

### 통합 워크플로우
- [ ] `integrated_crew.py` 실행 성공
- [ ] 전체 프로세스 순차 실행 확인
- [ ] 최종 리포트 생성 확인

### n8n 연동
- [ ] 워크플로우 임포트 완료
- [ ] PostgreSQL Credentials 설정
- [ ] 워크플로우 활성화
- [ ] 스케줄 설정 (필요 시)
- [ ] 수동 실행 테스트 성공

---

## 🚀 다음 단계

### Phase 4 개발 (Week 9-10)

1. **백테스팅 시스템**
   - `core/modules/backtesting.py` 구현
   - 과거 데이터 기반 전략 검증
   - 성과 리포트 자동 생성

2. **Alert Manager**
   - `core/agents/alert_manager.py` 완성
   - 실시간 모니터링
   - 알림 시스템 구축
   - n8n 알림 워크플로우 활성화

3. **페이퍼 트레이딩**
   - 가상 포트폴리오 관리
   - 매매 시뮬레이션
   - 성과 추적

---

**작성자**: Claude
**관련 문서**:
- [N8N_WORKFLOW_SETUP_GUIDE.md](N8N_WORKFLOW_SETUP_GUIDE.md)
- [IMPORT_PATH_FIX.md](IMPORT_PATH_FIX.md)
- [N8N_WORKFLOW_FIX.md](N8N_WORKFLOW_FIX.md)
