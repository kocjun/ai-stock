# n8n 워크플로우 실행 가이드

**작성일**: 2025-10-20
**목적**: n8n 워크플로우를 임포트하고 실행하는 방법

---

## 📋 사전 확인사항

### 1. Docker 컨테이너 상태 확인

```bash
docker ps
```

**필수 컨테이너**:
- ✅ `n8n` - Up 상태 (포트: 5678)
- ✅ `investment_postgres` - Up 상태 (포트: 5432)

만약 컨테이너가 중지되어 있다면:
```bash
cd /Users/yeongchang.jeon/workspace/ai-agent
docker-compose up -d
```

### 2. n8n 접속 확인

브라우저에서 n8n 접속:
```bash
open http://localhost:5678
```

**로그인 정보** (`.env` 파일 참조):
- 사용자: `admin` (또는 이메일)
- 비밀번호: `.env` 파일의 `N8N_BASIC_AUTH_PASSWORD` 값

---

## 🚀 워크플로우 임포트 방법

### 준비된 워크플로우 파일

프로젝트에 3개의 워크플로우가 준비되어 있습니다:

```
n8n_workflows/
├── data_collection_workflow.json     # 데이터 수집 자동화
├── alert_workflow.json                # 알림 자동화
└── weekly_analysis_workflow.json      # 주간 분석 자동화
```

---

## 📥 1. 데이터 수집 워크플로우 임포트

### 임포트 단계

1. **n8n 대시보드 접속**: http://localhost:5678

2. **새 워크플로우 생성**:
   - 왼쪽 상단 "+" 버튼 클릭 또는
   - "Add workflow" 클릭

3. **워크플로우 임포트**:
   - 오른쪽 상단 "..." (메뉴) 클릭
   - "Import from file" 선택
   - 파일 선택: `n8n_workflows/data_collection_workflow.json`
   - "Import" 클릭

4. **워크플로우 구조 확인**:
   ```
   [Schedule Trigger (매일 18시)]
         ↓
   [CrewAI 실행]
         ↓
   [성공 여부 확인]
         ↓
   [Slack 알림] → [PostgreSQL 로그]
   ```

### 설정 필요 항목

#### A. CrewAI 실행 노드
- **Node**: "CrewAI 실행"
- **Command**:
  ```bash
  cd /data/ai-agent && source .venv/bin/activate && python core/agents/investment_crew.py
  ```
- ⚠️ **주의**: Docker 컨테이너 내부에서 실행되므로 경로가 `/data/ai-agent`입니다.

**로컬에서 테스트 시 경로 수정**:
```bash
cd /Users/yeongchang.jeon/workspace/ai-agent && source .venv/bin/activate && python core/agents/investment_crew.py
```

#### B. PostgreSQL 연결 설정
- **Node**: "PostgreSQL 로그 저장"
- **Credentials**: PostgreSQL 연결 정보 입력
  - Host: `investment_postgres` (Docker 네트워크 내부) 또는 `localhost`
  - Port: `5432`
  - Database: `investment_db`
  - User: `invest_user`
  - Password: `.env` 파일의 `DB_PASSWORD` 값

#### C. Slack 알림 (선택사항)
- **Node**: "Slack 알림 (성공)" / "Slack 알림 (실패)"
- Slack Webhook URL 필요
- 없으면 해당 노드 비활성화 가능

### 워크플로우 저장 및 활성화

```
1. 오른쪽 상단 "Save" 클릭 → 워크플로우 이름 입력
2. 오른쪽 상단 토글 스위치 ON → 워크플로우 활성화
```

---

## 📥 2. Alert 워크플로우 임포트

### 파일: `n8n_workflows/alert_workflow.json`

### 워크플로우 구조
```
[Schedule Trigger (매일 09:30)]
      ↓
[Alert Manager 실행]
      ↓
[알림 있는지 확인]
      ↓
[Slack 알림] / [이메일 전송]
```

### 설정 필요 항목

#### A. Alert Manager 실행 노드
```bash
cd /Users/yeongchang.jeon/workspace/ai-agent && source .venv/bin/activate && python core/agents/alert_manager.py
```

⚠️ **주의**: `alert_manager.py`는 Phase 4에서 구현 예정입니다.

#### B. Slack Webhook URL
- **Node**: "Slack 알림 전송"
- Slack Incoming Webhook URL 필요
- 설정 방법: https://api.slack.com/messaging/webhooks

#### C. 이메일 설정 (선택사항)
- **Node**: "이메일 전송"
- SMTP 서버 정보 필요
- 또는 노드 비활성화

---

## 📥 3. 주간 분석 워크플로우 임포트

### 파일: `n8n_workflows/weekly_analysis_workflow.json`

### 워크플로우 구조
```
[Schedule Trigger (매주 토요일 09:00)]
      ↓
[주간 분석 스크립트 실행]
      ↓
[성공 확인]
      ↓
[성공 알림] / [실패 알림]
```

### 설정 필요 항목

#### A. 주간 분석 스크립트 경로
```bash
cd /path/to/ai-agent && ./scripts/run_weekly_analysis.sh
```

**실제 경로로 수정**:
```bash
cd /Users/yeongchang.jeon/workspace/ai-agent && ./scripts/run_weekly_analysis.sh
```

⚠️ **주의**: `run_weekly_analysis.sh` 스크립트는 Phase 4에서 생성 예정입니다.

#### B. Webhook URL 환경 변수
`.env` 파일에 설정:
```bash
N8N_WEBHOOK_URL=http://localhost:5678/webhook/weekly-report
```

---

## ✅ 워크플로우 테스트 방법

### 1. 수동 실행 테스트

각 워크플로우를 임포트한 후:

```
1. 워크플로우 열기
2. 오른쪽 상단 "Execute Workflow" 버튼 클릭
3. 실행 결과 확인
```

### 2. 데이터 수집 워크플로우 테스트

#### 방법 1: n8n에서 수동 실행
```
1. "한국 주식 데이터 수집 자동화" 워크플로우 열기
2. "Execute Workflow" 클릭
3. 각 노드 실행 결과 확인
```

#### 방법 2: 로컬에서 직접 실행
```bash
cd /Users/yeongchang.jeon/workspace/ai-agent
source .venv/bin/activate
python core/agents/investment_crew.py
```

#### 방법 3: Webhook 호출
```bash
curl -X POST http://localhost:5678/webhook/crew-webhook \
  -H "Content-Type: application/json" \
  -d '{
    "market": "KOSPI",
    "limit": 10,
    "days": 30
  }'
```

### 3. 실행 결과 확인

#### PostgreSQL 로그 확인
```bash
docker exec -it investment_postgres psql -U invest_user -d investment_db

# SQL 실행
SELECT * FROM data_collection_logs ORDER BY created_at DESC LIMIT 5;
```

#### n8n 실행 이력 확인
```
1. n8n 대시보드 접속
2. 왼쪽 메뉴 "Executions" 클릭
3. 최근 실행 이력 확인
```

---

## 🔧 문제 해결

### 1. "Command not found" 에러

**원인**: Python 경로 또는 가상환경 경로가 잘못됨

**해결**:
```bash
# 올바른 Python 경로 확인
which python3

# 가상환경 활성화 확인
source .venv/bin/activate
which python
```

워크플로우의 Command 수정:
```bash
cd /Users/yeongchang.jeon/workspace/ai-agent && \
  source .venv/bin/activate && \
  python core/agents/investment_crew.py
```

### 2. PostgreSQL 연결 실패

**원인**: 컨테이너 네트워크 또는 Credentials 문제

**해결**:

#### 컨테이너 내부에서 실행 시:
- Host: `investment_postgres` (Docker 네트워크 이름)

#### 로컬에서 실행 시:
- Host: `localhost` 또는 `127.0.0.1`

#### Credentials 확인:
```bash
# .env 파일 확인
cat .env | grep DB_

# 직접 연결 테스트
docker exec -it investment_postgres psql -U invest_user -d investment_db
```

### 3. "Module not found" 에러

**원인**: 의존성 패키지 미설치 또는 PYTHONPATH 문제

**해결**:
```bash
# 의존성 재설치
source .venv/bin/activate
pip install -r requirements.txt

# PYTHONPATH 설정
export PYTHONPATH=/Users/yeongchang.jeon/workspace/ai-agent:$PYTHONPATH
```

### 4. Slack 알림 실패

**원인**: Webhook URL 미설정 또는 잘못됨

**해결**:
- Slack Incoming Webhook 생성: https://api.slack.com/messaging/webhooks
- 워크플로우에서 올바른 URL 입력
- 또는 Slack 노드 비활성화 (테스트 시)

### 5. 스케줄이 실행되지 않음

**원인**: 워크플로우가 비활성화 상태

**해결**:
```
1. 워크플로우 열기
2. 오른쪽 상단 토글 스위치 확인 (ON으로 설정)
3. "Executions" 메뉴에서 실행 이력 확인
```

---

## 📊 워크플로우 스케줄

| 워크플로우 | 실행 시간 | 설명 |
|-----------|----------|------|
| **데이터 수집** | 매일 18:00 | 코스피 종목 데이터 수집 |
| **Alert Manager** | 매일 09:30 | 시장 오픈 직후 모니터링 |
| **주간 분석** | 매주 토요일 09:00 | 종합 투자 분석 리포트 |

---

## 🎯 다음 단계

### 1. Phase 4 개발 완료 후
- `alert_manager.py` 구현 완료 시 Alert 워크플로우 활성화
- `run_weekly_analysis.sh` 생성 후 주간 분석 워크플로우 활성화

### 2. 운영 환경 배포 시
- Slack Webhook URL 설정
- 이메일 SMTP 설정
- 스케줄 시간 조정 (필요 시)

### 3. 모니터링
- n8n Executions 메뉴에서 정기적으로 실행 이력 확인
- PostgreSQL 로그 테이블 확인
- 에러 발생 시 즉시 조치

---

## 📌 현재 상태 (2025-10-20)

### 동작 가능한 워크플로우
✅ **데이터 수집 워크플로우** (data_collection_workflow.json)
- `investment_crew.py` 구현 완료
- PostgreSQL 연동 완료
- 즉시 사용 가능

### 개발 예정 (Phase 4)
🔄 **Alert 워크플로우** (alert_workflow.json)
- `alert_manager.py` 구현 예정 (Week 10)

🔄 **주간 분석 워크플로우** (weekly_analysis_workflow.json)
- `run_weekly_analysis.sh` 생성 예정 (Week 10)

---

## 🚀 빠른 시작 체크리스트

- [ ] Docker 컨테이너 실행 확인 (`docker ps`)
- [ ] n8n 접속 확인 (http://localhost:5678)
- [ ] 데이터 수집 워크플로우 임포트
- [ ] PostgreSQL Credentials 설정
- [ ] 워크플로우 수동 실행 테스트
- [ ] 실행 결과 확인 (DB 로그 조회)
- [ ] 워크플로우 활성화 (스케줄 자동 실행)
- [ ] Executions 메뉴에서 실행 이력 모니터링

---

**작성자**: Claude
**참고 문서**:
- [N8N_SETUP.md](N8N_SETUP.md) - n8n 초기 설정
- [N8N_WORKFLOW_FIX.md](N8N_WORKFLOW_FIX.md) - 경로 수정 내역
