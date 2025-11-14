# n8n 워크플로 설정 가이드

## n8n 접속

1. **브라우저에서 접속**
   ```
   http://localhost:5678
   ```

2. **로그인 정보**
   - 사용자: `admin`
   - 비밀번호: `.env` 파일의 `N8N_BASIC_AUTH_PASSWORD` 참조

---

## PostgreSQL 연결 설정

### 1. Credentials 생성

n8n 인터페이스에서:

1. 좌측 메뉴 → **Credentials** 클릭
2. **+ New credential** 클릭
3. **Postgres** 선택
4. 다음 정보 입력:

```
Name: Investment PostgreSQL
Host: investment_postgres  (Docker 컨테이너 이름)
Database: investment_db
User: invest_user
Password: (.env의 DB_PASSWORD)
Port: 5432
SSL: disabled
```

5. **Test connection** → **Save** 클릭

---

## 웹훅 설정

### 1. 테스트 워크플로 생성

1. n8n 홈 → **+ New workflow** 클릭
2. 워크플로 이름: `테스트 - CrewAI 웹훅`

### 2. Webhook 노드 추가

1. **+** 버튼 → **Webhook** 노드 추가
2. 설정:
   ```
   HTTP Method: POST
   Path: crew-webhook
   Response Mode: Respond to Webhook
   ```
3. **Listen for Test Event** 클릭
4. 웹훅 URL 확인: `http://localhost:5678/webhook/crew-webhook`

### 3. 테스트 실행

터미널에서 다음 명령 실행:

```bash
curl -X POST http://localhost:5678/webhook/crew-webhook \
  -H "Content-Type: application/json" \
  -d '{
    "type": "test",
    "message": "Hello from CrewAI",
    "timestamp": "2025-10-12T21:00:00"
  }'
```

n8n에서 데이터 수신 확인 후 **Execute Workflow** 클릭

---

## 데이터 수집 자동화 워크플로 구축

### 워크플로 구조

```
[Schedule Trigger]  →  [HTTP Request]  →  [IF 조건]  →  [Slack/Email]
  (매일 18시)         (CrewAI 실행)      (성공/실패)     (알림)
                                              ↓
                                        [PostgreSQL]
                                         (로그 저장)
```

### 1. Schedule Trigger 노드

1. **Schedule Trigger** 노드 추가
2. 설정:
   ```
   Trigger Times: Custom
   Cron Expression: 0 18 * * *  (매일 18시)
   또는
   Trigger at Hour: 18
   ```

### 2. Execute Command 노드 (CrewAI 실행)

**옵션 A: Docker 외부에서 실행 (권장)**

1. **Execute Command** 노드 추가
2. 설정:
   ```
   Command: bash
   Arguments (JSON):
   [
     "-c",
     "cd /Users/yeongchang.jeon/workspace/ai-agent && source .venv/bin/activate && python investment_crew.py"
   ]
   ```

**옵션 B: HTTP Request로 외부 API 호출**

1. **HTTP Request** 노드 추가
2. 설정:
   ```
   Method: POST
   URL: http://host.docker.internal:8000/run-crew
   Body: JSON
   {
     "market": "KOSPI",
     "limit": 50,
     "days": 30
   }
   ```

### 3. Webhook 수신 노드

1. **Webhook** 노드 추가
2. 설정:
   ```
   HTTP Method: POST
   Path: crew-webhook
   Response Mode: Using 'Respond to Webhook' Node
   ```
3. CrewAI의 `N8N_WEBHOOK_URL`에서 이 URL을 호출

### 4. IF 조건 노드 (성공/실패 판단)

1. **IF** 노드 추가
2. 설정:
   ```
   Conditions:
   - Value 1: {{ $json.report }}
   - Operation: contains
   - Value 2: "성공"
   ```

### 5. Slack 알림 노드 (선택사항)

**성공 알림:**
```
Channel: #ai-agent-alerts
Message:
✅ 데이터 수집 완료

시장: {{ $json.market }}
종목 수: {{ $json.limit }}
기간: {{ $json.days }}일

{{ $json.report }}
```

**실패 알림:**
```
Channel: #ai-agent-alerts
Message:
⚠️ 데이터 수집 실패

{{ $json.report }}
```

### 6. PostgreSQL 로그 저장 노드

1. **Postgres** 노드 추가
2. Credential: 앞서 생성한 `Investment PostgreSQL` 선택
3. 설정:
   ```
   Operation: Execute Query
   Query:
   INSERT INTO data_collection_logs
   (timestamp, market, limit_count, days, status, report)
   VALUES
   (
     '{{ $json.timestamp }}',
     '{{ $json.market }}',
     {{ $json.limit }},
     {{ $json.days }},
     'success',
     '{{ $json.report }}'
   );
   ```

### 7. Respond to Webhook 노드

1. **Respond to Webhook** 노드 추가
2. 설정:
   ```
   Respond With: JSON
   Response Body:
   {
     "status": "success",
     "message": "Workflow completed",
     "timestamp": "{{ $now }}"
   }
   ```

---

## 로그 테이블 생성

워크플로 로그를 저장하기 위한 테이블:

```sql
-- PostgreSQL에 접속하여 실행
docker exec -it investment_postgres psql -U invest_user -d investment_db

CREATE TABLE IF NOT EXISTS data_collection_logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    market VARCHAR(10),
    limit_count INT,
    days INT,
    status VARCHAR(20),
    report TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_logs_timestamp ON data_collection_logs(timestamp DESC);
CREATE INDEX idx_logs_status ON data_collection_logs(status);
```

---

## 워크플로 테스트

### 1. 수동 실행 테스트

n8n 워크플로에서:
1. **Execute Workflow** 버튼 클릭
2. 실행 로그 확인
3. PostgreSQL에서 데이터 확인

```bash
docker exec investment_postgres psql -U invest_user -d investment_db \
  -c "SELECT * FROM data_collection_logs ORDER BY created_at DESC LIMIT 5;"
```

### 2. Webhook 테스트

```bash
curl -X POST http://localhost:5678/webhook/crew-webhook \
  -H "Content-Type: application/json" \
  -d '{
    "type": "data_collection_report",
    "market": "KOSPI",
    "limit": 50,
    "days": 30,
    "report": "테스트 리포트",
    "timestamp": "2025-10-12T21:00:00"
  }'
```

### 3. 스케줄 테스트

1. Schedule Trigger를 5분 후로 설정
2. **Activate** 워크플로 활성화
3. 5분 후 자동 실행 확인

---

## 문제 해결

### Webhook 연결 실패

**증상:** `n8n 연결 실패` 에러

**해결:**
```bash
# n8n 컨테이너 로그 확인
docker logs n8n

# 컨테이너 재시작
docker-compose restart n8n

# 네트워크 확인
docker network inspect investment_network
```

### PostgreSQL 연결 실패

**증상:** `connection refused` 또는 `authentication failed`

**해결:**
```bash
# PostgreSQL 상태 확인
docker exec investment_postgres pg_isready -U invest_user

# 비밀번호 확인
cat .env | grep DB_PASSWORD

# 컨테이너 간 통신 테스트
docker exec n8n ping investment_postgres
```

### CrewAI 실행 실패

**증상:** Execute Command에서 Python 에러

**해결:**
```bash
# 가상환경 확인
source .venv/bin/activate
python investment_crew.py

# Ollama 서버 확인
curl http://localhost:11434/api/tags

# 의존성 재설치
pip install -r requirements.txt
```

---

## 고급 설정

### 1. 에러 알림 강화

Error Trigger 노드 추가:
```
Trigger: On Workflow Error
Action: Send Slack/Email with error details
```

### 2. 재시도 로직

HTTP Request 노드에서:
```
Settings:
- Retry On Fail: enabled
- Max Tries: 3
- Wait Between Tries: 5000ms
```

### 3. 데이터 백업

추가 워크플로: 매주 일요일 00시
```
[Schedule Trigger] → [Postgres] → [Google Drive/S3]
                      (데이터 export)  (백업 저장)
```

---

## 다음 단계

1. ✅ 웹훅 테스트 완료
2. ✅ PostgreSQL 연동 확인
3. 🔄 스케줄 자동화 설정
4. 🔄 알림 채널 설정 (Slack/Email)
5. 🔄 모니터링 대시보드 구축

---

**작성일:** 2025-10-12
**버전:** 1.0
