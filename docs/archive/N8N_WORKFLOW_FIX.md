# n8n 워크플로우 경로 수정 완료

**수정 날짜**: 2025-10-20
**수정 이유**: 프로젝트 구조 변경 (모듈화) 반영

---

## 📋 수정 내역

프로젝트가 모듈화되면서 파일 경로가 변경되었으나, n8n 워크플로우의 실행 경로가 업데이트되지 않은 문제를 수정했습니다.

### 수정된 워크플로우 파일

#### 1. **data_collection_workflow.json**
데이터 수집 자동화 워크플로우

**변경 전**:
```json
"command": "cd /data/ai-agent && source .venv/bin/activate && python investment_crew.py"
```

**변경 후**:
```json
"command": "cd /data/ai-agent && source .venv/bin/activate && python core/agents/investment_crew.py"
```

**영향**:
- CrewAI 실행 노드가 올바른 경로에서 Data Curator 에이전트 실행
- 매일 18시 자동 데이터 수집 정상 작동

---

#### 2. **alert_workflow.json**
알림 자동화 워크플로우

**변경 전**:
```json
"command": "cd /Users/yeongchang.jeon/workspace/ai-agent && source .venv/bin/activate && python alert_manager.py"
```

**변경 후**:
```json
"command": "cd /Users/yeongchang.jeon/workspace/ai-agent && source .venv/bin/activate && python core/agents/alert_manager.py"
```

**영향**:
- Alert Manager 실행 노드가 올바른 경로에서 실행
- 매일 오전 9시 30분 시장 모니터링 알림 정상 작동

---

#### 3. **weekly_analysis_workflow.json**
주간 분석 자동화 워크플로우

**변경 전**:
```json
"command": "cd /path/to/ai-agent && ./run_weekly_analysis.sh"
```

**변경 후**:
```json
"command": "cd /path/to/ai-agent && ./scripts/run_weekly_analysis.sh"
```

**영향**:
- 주간 분석 스크립트가 올바른 경로에서 실행
- 매주 토요일 09:00 전체 투자 분석 정상 작동

---

## 🗂️ 새로운 프로젝트 구조

```
ai-agent/
├── core/
│   ├── agents/                   # ✅ 에이전트들 (이전 루트 위치에서 이동)
│   │   ├── investment_crew.py
│   │   ├── screening_crew.py
│   │   ├── risk_crew.py
│   │   ├── portfolio_crew.py
│   │   ├── integrated_crew.py
│   │   └── alert_manager.py
│   ├── modules/                  # 분석 모듈들
│   ├── tools/                    # CrewAI 도구들
│   └── utils/                    # 유틸리티
│
├── scripts/                      # ✅ 스크립트들 (이전 루트 위치에서 이동)
│   ├── run_daily_collection.sh
│   ├── run_weekly_analysis.sh
│   └── run_alerts.sh
│
└── n8n_workflows/                # n8n 워크플로우 정의
    ├── data_collection_workflow.json
    ├── alert_workflow.json
    └── weekly_analysis_workflow.json
```

---

## ✅ 검증 방법

### 1. n8n 워크플로우 재임포트

n8n 대시보드에서 기존 워크플로우를 삭제하고 수정된 파일을 다시 임포트:

```bash
# n8n 대시보드 접속
open http://localhost:5678

# 워크플로우 > Import from File
# 수정된 JSON 파일 선택:
# - n8n_workflows/data_collection_workflow.json
# - n8n_workflows/alert_workflow.json
# - n8n_workflows/weekly_analysis_workflow.json
```

### 2. 수동 테스트 실행

각 워크플로우의 "Execute Workflow" 버튼 클릭하여 정상 작동 확인

### 3. 경로 확인

```bash
# 프로젝트 루트에서 파일 존재 확인
ls -la core/agents/investment_crew.py
ls -la core/agents/alert_manager.py
ls -la scripts/run_weekly_analysis.sh

# 모든 파일이 존재해야 함
```

---

## 🔧 추가 필요한 조치

### 1. Docker 컨테이너 내부 경로 확인

`data_collection_workflow.json`이 Docker 컨테이너 내부(`/data/ai-agent`)에서 실행되는 경우:

```bash
# Docker 컨테이너 접속
docker exec -it n8n sh

# 경로 확인
ls -la /data/ai-agent/core/agents/investment_crew.py

# 없으면 볼륨 마운트 설정 확인
```

### 2. 스크립트 실행 권한 확인

```bash
# 스크립트 실행 권한 부여
chmod +x scripts/run_daily_collection.sh
chmod +x scripts/run_weekly_analysis.sh
chmod +x scripts/run_alerts.sh
```

### 3. PYTHONPATH 환경 변수 설정

새로운 모듈 구조에서 import가 정상 작동하도록:

```bash
# .env 파일에 추가
PYTHONPATH=/Users/yeongchang.jeon/workspace/ai-agent

# 또는 각 스크립트 시작 부분에 추가
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

---

## 📌 주의사항

### n8n 워크플로우 수정 시
1. **백업**: 기존 워크플로우를 Export하여 백업
2. **검증**: 수정 후 반드시 수동 실행으로 검증
3. **버전 관리**: Git에 변경사항 커밋

### 프로젝트 구조 변경 시
1. **n8n 워크플로우 동기화** 필수
2. **스크립트 내 경로** 업데이트
3. **import 구문** 수정
4. **문서** 업데이트

---

## 🎯 다음 단계

n8n 워크플로우 경로 수정이 완료되었으므로, Phase 4 개발을 진행할 수 있습니다:

1. ✅ **n8n 워크플로우 경로 수정 완료**
2. 🔄 **Phase 4 백테스팅 시스템 구현** (다음)
3. 🔄 **Alert Manager 구현**
4. 🔄 **페이퍼 트레이딩 시스템 구현**

---

**작성자**: Claude
**마지막 업데이트**: 2025-10-20
