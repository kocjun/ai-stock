
# 🤖 한국 주식시장 AI 투자 분석 에이전트

코스피 상장사의 재무 데이터와 시장 정보를 분석하여 투자 참고 정보를 제공하는 AI 에이전트 시스템

**🎉 프로젝트 완료 + 페이퍼 트레이딩 준비 완료** (2025-10-18)

---

## ✨ 주요 기능

### 📊 AI 분석 시스템 (완료)
- ✅ 5개 AI 에이전트: Data Curator, Screening Analyst, Risk Manager, Portfolio Planner, Alert Manager
- ✅ 9개 CrewAI 도구 (데이터 수집, 분석, 백테스팅, 알림)
- ✅ 완전 자동화된 투자 분석 워크플로 (일간/주간)
- ✅ 백테스팅 시스템 (9개 성과 지표 + 벤치마크 비교)
- ✅ Alert Manager (가격/손절/리밸런싱 알림)

### 🎮 페이퍼 트레이딩 (구현 완료 ✅)
- ✅ 가상 계좌 시스템
- ✅ 실시간 매매 시뮬레이션 (매수/매도)
- ✅ 자동 포트폴리오 관리 (손절/익절)
- ✅ 성과 분석 리포트
- ✅ **실시간 웹 대시보드** (Dash/Plotly)
- ✅ **통합 테스트 계획** (End-to-End)

---

## 📁 프로젝트 구조

```
ai-agent/
├── 📁 core/                    # 핵심 분석 시스템
│   ├── agents/                # AI 에이전트 (6개)
│   ├── modules/               # 분석 모듈 (6개)
│   ├── tools/                 # CrewAI 도구 (10개)
│   └── utils/                 # 유틸리티
│
├── 📁 paper_trading/          # 페이퍼 트레이딩 시스템 ✅
│   ├── dashboard.py           # 실시간 웹 대시보드
│   ├── trading_crew.py        # AI 자동 매매
│   ├── paper_trading.py       # 매수/매도 실행
│   ├── portfolio_manager.py   # 포트폴리오 관리
│   └── performance_reporter.py # 성과 보고서
│
├── 📁 tests/                  # 테스트 파일
│   ├── run_integration_test.sh # 통합 테스트 스크립트 ✅
│   └── TEST_CHECKLIST.md      # 테스트 체크리스트 ✅
├── 📁 scripts/                # 실행 스크립트
├── 📁 docs/                   # 문서
├── 📁 docker/                 # Docker 설정
├── 📁 n8n_workflows/          # n8n 워크플로
│
├── 📁 logs/                   # 로그 파일
├── 📁 reports/                # 분석 리포트
├── 📁 postgres-data/          # DB 데이터
└── 📁 n8n-data/               # n8n 데이터
```

---

## 🚀 빠른 시작

### 1. 사전 요구사항

#### 필수 설치
- **Docker Desktop**: PostgreSQL + n8n 실행
- **Python 3.11+**: AI 에이전트 실행
- **Ollama**: 로컬 LLM 서버

```bash
# Ollama 설치 (macOS)
brew install ollama

# 모델 다운로드
ollama pull llama3.1:8b

# 확인
ollama list
```

### 2. 환경 설정

```bash
# 1. 가상환경 생성
python3 -m venv .venv
source .venv/bin/activate

# 2. 의존성 설치
pip install -r requirements.txt

# 3. 환경 변수 설정
cp .env.example .env  # .env 파일 수정 필요
```

### 3. Docker 서비스 실행

```bash
# PostgreSQL + n8n 실행
cd docker
docker-compose up -d

# 상태 확인
docker ps

# 로그 확인
docker-compose logs -f
```

### 4. 데이터 수집

```bash
# 한 번만 실행 (초기 데이터 수집)
source .venv/bin/activate
python core/utils/collect_data.py
```

> Docker 컨테이너(`ai-stock-app`)에서 운영한다면 다음 명령으로 종목/가격 데이터와 가상 계좌를 한 번에 부트스트랩할 수 있습니다.
>
> ```bash
> cd docker
> docker compose --env-file ../.env exec ai-stock-app \
>   bash -lc "python scripts/bootstrap_data.py"
> ```

### 5. 자동화 설정

```bash
# cron job 설정 (일간/주간 자동 실행)
./scripts/setup_cron.sh

# 알림 자동화 추가 (선택)
./scripts/add_alert_cron.sh
```

---

## 💻 사용 방법

### 📊 분석 시스템

#### 수동 실행

```bash
# 가상환경 활성화
source .venv/bin/activate

# 1. 데이터 수집
python core/agents/investment_crew.py

# 2. 종목 스크리닝
python core/agents/screening_crew.py

# 3. 리스크 분석
python core/agents/risk_crew.py

# 4. 포트폴리오 최적화
python core/agents/portfolio_crew.py

# 5. 통합 분석
python core/agents/integrated_crew.py

# 6. 알림 체크
python core/agents/alert_manager.py
```

#### 자동 실행 (cron)

설정 후 자동으로 실행됩니다:
- **매일 18:00**: 데이터 수집
- **매일 08:30, 16:00**: 알림 체크 (평일만)
- **매주 토요일 09:00**: 주간 종합 분석

```bash
# cron job 확인
crontab -l

# 로그 확인
tail -f logs/cron_daily.log
tail -f logs/cron_alerts.log
```

### 🧪 테스트

```bash
source .venv/bin/activate

# 1. 데이터 수집 테스트
python tests/test_fdr.py

# 2. 도구 테스트
python tests/test_tools.py

# 3. Phase 2 분석 테스트
python tests/test_phase2.py

# 4. Phase 3 통합 테스트
python tests/test_phase3.py

# 5. 백테스팅 테스트
python tests/test_backtesting.py
```

---

## 📊 주요 에이전트

### 1. Data Curator
**역할**: 데이터 수집 및 품질 관리
- 종목 리스트 수집
- 가격 데이터 수집
- 데이터 품질 검증

### 2. Screening Analyst
**역할**: 종목 선정 및 팩터 분석
- 재무 지표 계산 (PER, PBR, ROE 등)
- 팩터 스코어링 (가치/성장/수익성/모멘텀/안정성)
- 투자 종목 추천

### 3. Risk Manager
**역할**: 리스크 분석 및 관리
- 변동성, MDD, VaR 계산
- Sharpe Ratio 분석
- 포트폴리오 리스크 평가

### 4. Portfolio Planner
**역할**: 포트폴리오 최적화
- 동일가중/시총가중/리스크패리티
- 자산 배분
- 리밸런싱 계획

### 5. Alert Manager
**역할**: 시장 모니터링 및 알림
- 가격 급락/급등 감지
- 손절선/목표가 알림
- 리밸런싱 시점 알림

---

## 📚 문서

### 개발 및 운영
- **[CLAUDE.md](docs/CLAUDE.md)**: 개발 가이드 및 코드 패턴
- **[PAPER_TRADING_PLAN.md](docs/PAPER_TRADING_PLAN.md)**: 페이퍼 트레이딩 설계
- **[PAPER_TRADING_IMPLEMENTATION.md](docs/PAPER_TRADING_IMPLEMENTATION.md)**: 구현 상세
- **[ALERT_GUIDE.md](docs/ALERT_GUIDE.md)**: 알림 시스템 가이드
- **[N8N_SETUP.md](docs/N8N_SETUP.md)**: n8n 워크플로 설정
- **[monitoring_guide.md](docs/monitoring_guide.md)**: 시스템 모니터링

### 테스트
- **[INTEGRATION_TEST_PLAN.md](docs/INTEGRATION_TEST_PLAN.md)**: 통합 테스트 계획 ✅
- **[TEST_CHECKLIST.md](tests/TEST_CHECKLIST.md)**: 테스트 체크리스트 ✅
- 컨테이너 환경에서 통합 테스트를 실행하려면 `./scripts/run_tests_in_container.sh` 스크립트를 사용하세요.
- 운영 재기동/검증 절차는 **[OPERATIONS_RUNBOOK.md](docs/OPERATIONS_RUNBOOK.md)** 참고

---

## 🔧 설정

### 환경 변수 (.env)

```bash
# Ollama LLM 설정
OPENAI_API_BASE=http://127.0.0.1:11434
OPENAI_MODEL_NAME=llama3.1:8b
OPENAI_MODEL_FALLBACK=llama3.1:8b
OPENAI_API_KEY=ollama
CREWAI_LLM_PROVIDER=ollama

# PostgreSQL 설정
DB_HOST=localhost
DB_PORT=5432
DB_NAME=investment_db
DB_USER=invest_user
DB_PASSWORD=your_password_here

# n8n 설정
N8N_WEBHOOK_URL=http://localhost:5678/webhook/crew-webhook
N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD=your_password_here

# CrewAI 설정
CREWAI_STORAGE_DIR=.crewai/
```

> **NAS 또는 원격 서버에서 내부망 LLM을 사용할 경우** `OPENAI_API_BASE`에 해당 서버 주소(예: `http://192.168.10.58:11434`)를 지정하면 됩니다. 모든 실행/테스트 스크립트는 이 값을 기반으로 헬스체크를 수행합니다.

### Docker 서비스

**PostgreSQL**:
- 포트: `5432`
- 데이터베이스: `investment_db`
- 사용자: `invest_user`

**n8n**:
- 포트: `5678`
- URL: `http://localhost:5678`
- 인증: admin / (설정한 비밀번호)

### Synology NAS / Docker 실행

Synology NAS에서 Python 3.10+를 수동 설치하기 어렵다면 Docker 컨테이너를 통해 애플리케이션을 실행할 수 있습니다.

1. `.env` 파일에 데이터베이스/LLM 설정을 입력합니다 (`OPENAI_API_BASE`는 내부망 LLM 주소로 지정).
2. Docker Compose 실행:
   ```bash
   cd docker
   docker compose build ai-stock-app
   docker compose up -d postgres n8n ai-stock-app
   ```
3. 컨테이너 내에서 명령 실행:
   ```bash
   docker compose exec ai-stock-app bash    # 쉘 접속
   python core/agents/integrated_crew.py    # 예: 통합 에이전트 실행
   ```

`ai-stock-app` 컨테이너는 호스트 워크스페이스를 `/app`으로 마운트하며 `.env`를 자동으로 로드합니다. LLM, PostgreSQL 등 모든 의존성은 동일한 네트워크(`investment_network`)에서 접근 가능합니다.

---

## 📈 데이터베이스

### 주요 테이블

- **stocks**: 종목 마스터 (50개)
- **prices**: 일별 가격 데이터 (~1,000건)
- **financials**: 분기별 재무제표
- **news_summary**: 뉴스 요약
- **data_collection_logs**: 수집 로그

### 데이터 확인

```bash
# PostgreSQL 접속
docker exec -it investment_postgres psql -U invest_user -d investment_db

# 데이터 현황
SELECT
    (SELECT COUNT(*) FROM stocks) as 종목수,
    (SELECT COUNT(*) FROM prices) as 가격데이터,
    (SELECT MAX(date) FROM prices) as 최근일자;
```

---

## 🐛 문제 해결

### Docker 서비스 재시작

```bash
cd docker
docker-compose restart
```

### Ollama 연결 확인

```bash
# Ollama 서버 확인
curl http://localhost:11434/api/tags

# 모델 확인
ollama list
```

### 로그 확인

```bash
# 데이터 수집 로그
tail -f logs/cron_daily.log

# 알림 로그
tail -f logs/cron_alerts.log

# 주간 분석 로그
tail -f logs/cron_weekly.log
```

### 데이터베이스 초기화

```bash
# 주의: 모든 데이터 삭제됨!
cd docker
docker-compose down -v
docker-compose up -d
```

---

## ⚠️ 면책 조항

```
본 프로젝트는 교육 및 연구 목적의 시스템입니다.

- 실제 투자 권유가 아닙니다
- 과거 성과가 미래 수익을 보장하지 않습니다
- 모든 투자 결정은 본인 책임입니다
- 데이터는 개인 분석 용도로만 사용하세요 (재배포 금지)
```

---

## 📞 지원

### 문제 보고
GitHub Issues를 통해 문제를 보고해주세요.

### 문서
- [CLAUDE.md](docs/CLAUDE.md): 개발 가이드
- [docs/](docs/) 폴더의 각종 문서 참조

---

**마지막 업데이트**: 2025-10-18
**버전**: 2.0 (구조 개편)
**프로젝트 상태**: ✅ 분석 시스템 완료 / 📋 페이퍼 트레이딩 설계 완료
