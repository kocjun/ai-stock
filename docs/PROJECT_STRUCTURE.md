# 📁 프로젝트 구조 가이드

프로젝트가 깔끔하게 재구성되었습니다. (2025-10-18)

---

## 🗂️ 디렉터리 구조

```
ai-agent/
├── core/                          # 핵심 분석 시스템
│   ├── agents/                   # AI 에이전트들
│   │   ├── investment_crew.py
│   │   ├── screening_crew.py
│   │   ├── risk_crew.py
│   │   ├── portfolio_crew.py
│   │   ├── integrated_crew.py
│   │   └── alert_manager.py
│   ├── modules/                  # 분석 모듈들
│   │   ├── financial_metrics.py
│   │   ├── technical_indicators.py
│   │   ├── factor_scoring.py
│   │   ├── risk_analysis.py
│   │   ├── portfolio_optimization.py
│   │   └── backtesting.py
│   ├── tools/                    # CrewAI 도구들
│   │   ├── data_collection_tool.py
│   │   ├── data_quality_tool.py
│   │   ├── financial_analysis_tool.py
│   │   ├── technical_analysis_tool.py
│   │   ├── risk_analysis_tool.py
│   │   ├── portfolio_tool.py
│   │   ├── backtesting_tool.py
│   │   ├── alert_tool.py
│   │   └── n8n_webhook_tool.py
│   └── utils/                    # 유틸리티
│       ├── db_utils.py
│       └── collect_data.py
│
├── paper_trading/                # 페이퍼 트레이딩 시스템
│   └── (향후 개발)
│
├── tests/                        # 테스트 파일들
│   ├── test_fdr.py
│   ├── test_tools.py
│   ├── test_phase2.py
│   ├── test_phase3.py
│   └── test_backtesting.py
│
├── scripts/                      # 실행 스크립트들
│   ├── run_daily_collection.sh
│   ├── run_weekly_analysis.sh
│   ├── run_alerts.sh
│   ├── setup_cron.sh
│   └── add_alert_cron.sh
│
├── docs/                         # 문서들
│   ├── CLAUDE.md
│   ├── investment_agent.md
│   ├── N8N_SETUP.md
│   ├── ALERT_GUIDE.md
│   ├── monitoring_guide.md
│   ├── PAPER_TRADING_PLAN.md
│   ├── WEEK2_SUMMARY.md
│   ├── PHASE2_SUMMARY.md
│   └── PHASE4_SUMMARY.md
│
├── docker/                       # Docker 설정
│   ├── docker-compose.yml
│   ├── docker-compose.n8n.yml
│   ├── Dockerfile.n8n
│   └── init-db.sql
│
├── n8n_workflows/                # n8n 워크플로
│   ├── data_collection_workflow.json
│   ├── alert_workflow.json
│   └── weekly_analysis_workflow.json
│
├── logs/                         # 로그 파일들
├── reports/                      # 분석 리포트들
├── postgres-data/                # PostgreSQL 데이터
├── n8n-data/                     # n8n 데이터
│
├── .env                          # 환경 변수
├── .gitignore
├── requirements.txt
├── README.md                     # 메인 README
└── PROJECT_STRUCTURE.md          # 이 파일
```

---

## 📦 모듈 설명

### core/agents/
**AI 에이전트들** - CrewAI 기반 자율 에이전트

| 파일 | 역할 | 주요 기능 |
|------|------|----------|
| investment_crew.py | Data Curator | 데이터 수집, 품질 검증 |
| screening_crew.py | Screening Analyst | 종목 스크리닝, 팩터 분석 |
| risk_crew.py | Risk Manager | 리스크 분석, VaR, MDD |
| portfolio_crew.py | Portfolio Planner | 포트폴리오 최적화 |
| integrated_crew.py | 통합 워크플로 | 전체 분석 프로세스 |
| alert_manager.py | Alert Manager | 시장 모니터링, 알림 |

### core/modules/
**분석 모듈들** - 핵심 로직 구현

| 파일 | 기능 |
|------|------|
| financial_metrics.py | 재무 지표 계산 (PER, PBR, ROE 등) |
| technical_indicators.py | 기술적 지표 (SMA, RSI, MACD 등) |
| factor_scoring.py | 팩터 스코어링 시스템 |
| risk_analysis.py | 리스크 분석 (변동성, Sharpe 등) |
| portfolio_optimization.py | 포트폴리오 최적화 알고리즘 |
| backtesting.py | 백테스팅 엔진 |

### core/tools/
**CrewAI 도구들** - 에이전트가 사용하는 도구

| 파일 | 설명 |
|------|------|
| data_collection_tool.py | FinanceDataReader 연동 |
| data_quality_tool.py | 데이터 품질 체크 |
| financial_analysis_tool.py | 재무 분석 도구 |
| technical_analysis_tool.py | 기술적 분석 도구 |
| risk_analysis_tool.py | 리스크 분석 도구 |
| portfolio_tool.py | 포트폴리오 관리 도구 |
| backtesting_tool.py | 백테스팅 도구 |
| alert_tool.py | 알림 도구 |
| n8n_webhook_tool.py | n8n 연동 도구 |

### core/utils/
**유틸리티** - 공통 기능

| 파일 | 기능 |
|------|------|
| db_utils.py | PostgreSQL 연결 및 헬퍼 |
| collect_data.py | 간단한 데이터 수집 스크립트 |

---

## 🔧 사용 방법

### 1. 에이전트 실행

```bash
# 가상환경 활성화
source .venv/bin/activate

# 에이전트 실행 (core/agents/ 에서)
python core/agents/investment_crew.py
python core/agents/screening_crew.py
python core/agents/integrated_crew.py
```

### 2. 모듈 직접 사용

```python
# Python 스크립트에서 import
from core.modules.financial_metrics import calculate_basic_ratios
from core.modules.risk_analysis import calculate_portfolio_risk
from core.utils.db_utils import get_db_connection

# 사용
conn = get_db_connection()
# ... 분석 로직
```

### 3. 스크립트 실행

```bash
# 스크립트 실행 (scripts/ 에서)
./scripts/run_daily_collection.sh
./scripts/run_alerts.sh
./scripts/run_weekly_analysis.sh
```

### 4. 테스트 실행

```bash
# 테스트 실행 (tests/ 에서)
python tests/test_fdr.py
python tests/test_phase2.py
```

---

## 🎯 Import 가이드

### 새로운 import 방식

```python
# ❌ 이전 (루트에서 직접 import)
from investment_crew import ...
from financial_metrics import ...
from tools.data_collection_tool import ...

# ✅ 현재 (모듈화된 import)
from core.agents.investment_crew import ...
from core.modules.financial_metrics import ...
from core.tools.data_collection_tool import ...
from core.utils.db_utils import get_db_connection
```

### 상대 경로 import (같은 패키지 내에서)

```python
# core/agents/screening_crew.py 내에서
from ..modules import financial_metrics
from ..tools import financial_analysis_tool
from ..utils import db_utils
```

---

## 📝 코드 작성 가이드

### 새 에이전트 추가

1. `core/agents/`에 파일 생성
2. CrewAI Agent 정의
3. Task 정의
4. Crew 생성 및 실행

```python
# core/agents/new_agent.py
from crewai import Agent, Task, Crew, LLM
from ..tools.xxx_tool import XxxTool

def create_agent():
    agent = Agent(
        role="New Agent",
        goal="...",
        backstory="...",
        tools=[XxxTool()]
    )
    return agent
```

### 새 모듈 추가

1. `core/modules/`에 파일 생성
2. 분석 로직 구현
3. `core/tools/`에 CrewAI Tool 래퍼 생성

```python
# core/modules/new_module.py
def analyze_something(data):
    # 분석 로직
    return result

# core/tools/new_tool.py
from crewai.tools import BaseTool
from ..modules.new_module import analyze_something

class NewTool(BaseTool):
    name = "new_tool"
    description = "..."
    
    def _run(self, input):
        return analyze_something(input)
```

---

## 🔄 마이그레이션 노트

### 변경 사항 요약

**이전 구조 (루트 폴더에 모든 파일)**:
```
ai-agent/
├── investment_crew.py
├── screening_crew.py
├── financial_metrics.py
├── technical_indicators.py
├── tools/
│   └── ...
└── ...
```

**현재 구조 (모듈화)**:
```
ai-agent/
├── core/
│   ├── agents/
│   ├── modules/
│   ├── tools/
│   └── utils/
├── paper_trading/
├── tests/
├── scripts/
└── docs/
```

### 장점

1. **명확한 분리**: 분석 시스템 vs 페이퍼 트레이딩
2. **확장 용이**: 새 기능 추가 시 명확한 위치
3. **유지보수 개선**: 모듈별 독립적 관리
4. **테스트 분리**: 테스트 코드 별도 관리
5. **문서화**: 문서들을 docs/에 통합

---

## 🐛 트러블슈팅

### Import 오류

**문제**: `ModuleNotFoundError: No module named 'core'`

**해결**:
```bash
# 프로젝트 루트에서 실행
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
python core/agents/investment_crew.py

# 또는 스크립트에서
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
```

### Docker 경로 오류

**문제**: `docker-compose.yml not found`

**해결**:
```bash
# docker/ 디렉터리로 이동
cd docker
docker-compose up -d

# 또는 루트에서
docker-compose -f docker/docker-compose.yml up -d
```

### 스크립트 실행 오류

**문제**: 스크립트에서 파일을 찾을 수 없음

**해결**:
```bash
# scripts/ 파일들은 상대 경로 사용
cd /path/to/ai-agent  # 프로젝트 루트로 이동
./scripts/run_daily_collection.sh
```

---

## 📚 다음 읽을 문서

- **[README.md](README.md)**: 프로젝트 개요 및 빠른 시작
- **[docs/CLAUDE.md](docs/CLAUDE.md)**: 개발 가이드
- **[docs/PAPER_TRADING_PLAN.md](docs/PAPER_TRADING_PLAN.md)**: 페이퍼 트레이딩 설계
- **[docs/ALERT_GUIDE.md](docs/ALERT_GUIDE.md)**: 알림 시스템 가이드

---

**마지막 업데이트**: 2025-10-18
**버전**: 2.0
