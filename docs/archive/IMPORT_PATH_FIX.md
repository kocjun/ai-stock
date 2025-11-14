# Import 경로 수정 완료

**작성일**: 2025-10-20
**이유**: 프로젝트 모듈화로 인한 경로 변경

---

## 📋 문제 상황

프로젝트 구조를 모듈화하면서 파일 위치가 변경되었으나, import 경로가 업데이트되지 않아 `ModuleNotFoundError` 발생

### 에러 예시
```
ModuleNotFoundError: No module named 'tools'
ModuleNotFoundError: No module named 'db_utils'
ModuleNotFoundError: No module named 'financial_metrics'
```

---

## ✅ 수정 내역

### 1. 에이전트 파일 (core/agents/*.py)

**변경 전**:
```python
from tools.data_collection_tool import DataCollectionTool
from tools.financial_analysis_tool import FinancialAnalysisTool
```

**변경 후**:
```python
from core.tools.data_collection_tool import DataCollectionTool
from core.tools.financial_analysis_tool import FinancialAnalysisTool
```

**영향 받은 파일**:
- `core/agents/investment_crew.py`
- `core/agents/screening_crew.py`
- `core/agents/risk_crew.py`
- `core/agents/portfolio_crew.py`
- `core/agents/integrated_crew.py`
- `core/agents/alert_manager.py`

---

### 2. 도구 파일 (core/tools/*.py)

**변경 전**:
```python
from db_utils import get_db_connection
from financial_metrics import analyze_stock_fundamentals
from factor_scoring import screen_stocks
```

**변경 후**:
```python
from core.utils.db_utils import get_db_connection
from core.modules.financial_metrics import analyze_stock_fundamentals
from core.modules.factor_scoring import screen_stocks
```

**영향 받은 파일**:
- `core/tools/data_collection_tool.py`
- `core/tools/data_quality_tool.py`
- `core/tools/financial_analysis_tool.py`
- `core/tools/technical_analysis_tool.py`
- `core/tools/risk_analysis_tool.py`
- `core/tools/portfolio_tool.py`

---

### 3. 분석 모듈 (core/modules/*.py)

**변경 전**:
```python
from db_utils import get_db_connection
from financial_metrics import calculate_metrics
```

**변경 후**:
```python
from core.utils.db_utils import get_db_connection
from core.modules.financial_metrics import calculate_metrics
```

**영향 받은 파일**:
- `core/modules/financial_metrics.py`
- `core/modules/factor_scoring.py`
- `core/modules/technical_indicators.py`
- `core/modules/risk_analysis.py`
- `core/modules/portfolio_optimization.py`

---

### 4. tools/__init__.py 수정

**Phase 4 미구현 도구 주석 처리**:

```python
# Phase 4 구현 예정
# from .backtesting_tool import BacktestingTool
# from .alert_tool import AlertTool
```

**이유**: `backtesting_tool.py`와 `alert_tool.py`는 Phase 4에서 구현 예정이므로 import 시 에러 방지

---

## 🔧 수정 방법

### 자동 일괄 수정 (sed 사용)

```bash
# 에이전트 파일 수정
find core/agents -name "*.py" -type f -exec sed -i '' \
  's/from tools\./from core.tools./g' {} \;

# 도구 파일 수정
find core/tools -name "*.py" -type f -exec sed -i '' \
  -e 's/^from db_utils/from core.utils.db_utils/g' \
  -e 's/^from financial_metrics/from core.modules.financial_metrics/g' \
  -e 's/^from factor_scoring/from core.modules.factor_scoring/g' \
  -e 's/^from technical_indicators/from core.modules.technical_indicators/g' \
  -e 's/^from risk_analysis/from core.modules.risk_analysis/g' \
  -e 's/^from portfolio_optimization/from core.modules.portfolio_optimization/g' \
  {} \;

# 분석 모듈 수정
find core/modules -name "*.py" -type f -exec sed -i '' \
  -e 's/^from db_utils/from core.utils.db_utils/g' \
  -e 's/^import db_utils/import core.utils.db_utils as db_utils/g' \
  -e 's/^from financial_metrics/from core.modules.financial_metrics/g' \
  -e 's/^from factor_scoring/from core.modules.factor_scoring/g' \
  -e 's/^from technical_indicators/from core.modules.technical_indicators/g' \
  -e 's/^from risk_analysis/from core.modules.risk_analysis/g' \
  -e 's/^from portfolio_optimization/from core.modules.portfolio_optimization/g' \
  {} \;
```

---

## ✅ 검증

### 1. Import 테스트

```bash
source .venv/bin/activate
python test_import.py
```

**결과**:
```
✓ DataCollectionTool imported
✓ DataQualityTool imported
✓ N8nWebhookTool imported
✓ DataCollectionTool instance created
✓ DataQualityTool instance created
✅ All imports successful!
```

### 2. 에이전트 실행 테스트

```bash
# Data Curator 실행
python core/agents/investment_crew.py

# Screening Analyst 실행
python core/agents/screening_crew.py

# 통합 워크플로우 실행
python core/agents/integrated_crew.py
```

---

## 📁 최종 프로젝트 구조

```
ai-agent/
├── core/
│   ├── agents/           # AI 에이전트 (import: core.agents.*)
│   │   ├── investment_crew.py
│   │   ├── screening_crew.py
│   │   ├── risk_crew.py
│   │   ├── portfolio_crew.py
│   │   ├── integrated_crew.py
│   │   └── alert_manager.py
│   │
│   ├── modules/          # 분석 모듈 (import: core.modules.*)
│   │   ├── financial_metrics.py
│   │   ├── factor_scoring.py
│   │   ├── technical_indicators.py
│   │   ├── risk_analysis.py
│   │   └── portfolio_optimization.py
│   │
│   ├── tools/            # CrewAI 도구 (import: core.tools.*)
│   │   ├── __init__.py
│   │   ├── data_collection_tool.py
│   │   ├── data_quality_tool.py
│   │   ├── financial_analysis_tool.py
│   │   ├── technical_analysis_tool.py
│   │   ├── risk_analysis_tool.py
│   │   ├── portfolio_tool.py
│   │   └── n8n_webhook_tool.py
│   │
│   └── utils/            # 유틸리티 (import: core.utils.*)
│       └── db_utils.py
│
├── scripts/              # 실행 스크립트
│   └── run_daily_collection.sh
│
├── tests/                # 테스트
│   └── test_phase*.py
│
└── test_import.py        # Import 검증 스크립트
```

---

## 🎯 Import 규칙

### 에이전트에서 도구 임포트
```python
# ✅ 올바른 방법
from core.tools.data_collection_tool import DataCollectionTool

# ❌ 잘못된 방법
from tools.data_collection_tool import DataCollectionTool
```

### 도구에서 모듈 임포트
```python
# ✅ 올바른 방법
from core.modules.financial_metrics import analyze_stock_fundamentals
from core.utils.db_utils import get_db_connection

# ❌ 잘못된 방법
from financial_metrics import analyze_stock_fundamentals
from db_utils import get_db_connection
```

### 모듈 간 임포트
```python
# ✅ 올바른 방법
from core.modules.financial_metrics import calculate_metrics
from core.utils.db_utils import get_db_connection

# ❌ 잘못된 방법
from financial_metrics import calculate_metrics
from db_utils import get_db_connection
```

---

## 📌 주의사항

### 1. Phase 4 개발 시

새로운 도구나 모듈을 추가할 때:

```python
# core/tools/__init__.py에 추가
from .backtesting_tool import BacktestingTool
from .alert_tool import AlertTool

__all__ = [
    # 기존 도구들...
    "BacktestingTool",
    "AlertTool",
]
```

### 2. n8n 워크플로우에서 실행 시

프로젝트 루트에서 실행해야 import가 정상 작동:

```bash
# ✅ 올바른 방법
cd /Users/yeongchang.jeon/workspace/ai-agent
python core/agents/investment_crew.py

# ❌ 잘못된 방법
cd /Users/yeongchang.jeon/workspace/ai-agent/core/agents
python investment_crew.py  # ModuleNotFoundError 발생!
```

### 3. PYTHONPATH 설정 (선택사항)

필요 시 환경 변수 설정:

```bash
# .env 파일에 추가
PYTHONPATH=/Users/yeongchang.jeon/workspace/ai-agent

# 또는 스크립트에서
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

---

## ✅ 완료 체크리스트

- [x] 에이전트 파일 import 경로 수정
- [x] 도구 파일 import 경로 수정
- [x] 모듈 파일 import 경로 수정
- [x] tools/__init__.py 업데이트
- [x] Import 테스트 스크립트 작성
- [x] 검증 완료
- [x] 문서화 완료

---

**작성자**: Claude
**관련 문서**:
- [N8N_WORKFLOW_FIX.md](N8N_WORKFLOW_FIX.md) - n8n 워크플로우 경로 수정
- [N8N_WORKFLOW_SETUP_GUIDE.md](N8N_WORKFLOW_SETUP_GUIDE.md) - 워크플로우 실행 가이드
