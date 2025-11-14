# 2주차 작업 완료 보고서

## 작업 기간
2025-10-12

## 목표
- CrewAI Data Curator 에이전트 구현
- n8n 워크플로 연동 테스트
- 데이터 수집 자동화 파이프라인 구축

---

## 완료된 작업

### 1. CrewAI Data Curator 에이전트 구현 ✅

#### 커스텀 도구 개발
새로운 `tools/` 디렉터리 생성 및 3개 도구 구현:

1. **DataCollectionTool** ([tools/data_collection_tool.py](tools/data_collection_tool.py))
   - 종목 리스트 수집 (`collect_stocks`)
   - 가격 데이터 수집 (`collect_prices`)
   - 통합 수집 (`collect_all`)
   - FinanceDataReader 연동

2. **DataQualityTool** ([tools/data_quality_tool.py](tools/data_quality_tool.py))
   - 전체 데이터 품질 체크
   - 종목/가격 데이터 검증
   - 커버리지 분석
   - 이상치 감지

3. **N8nWebhookTool** ([tools/n8n_webhook_tool.py](tools/n8n_webhook_tool.py))
   - n8n 워크플로 트리거
   - JSON 직렬화 및 전송
   - 에러 핸들링

#### Investment Crew 구현
[investment_crew.py](investment_crew.py) 작성:

- **Data Curator 에이전트**
  - 역할: 금융 데이터 엔지니어 (10년 경력)
  - 목표: 데이터 수집 및 품질 검증
  - 도구: DataCollectionTool, DataQualityTool

- **3개 순차 태스크**
  1. 데이터 수집: 종목 + 가격 데이터
  2. 품질 검증: 통계 및 이슈 확인
  3. 리포트 작성: 마크다운 형식 최종 보고서

- **LLM 통합**
  - Ollama 로컬 서버 (llama3.1:8b)
  - OpenAI 호환 API 사용
  - 환경 변수 기반 설정

#### 테스트 결과
[test_tools.py](test_tools.py) 실행 결과:

```
✓ DataCollectionTool: 정상 작동
  - 종목 리스트 수집: 50개 성공
  - 가격 데이터 수집: 750 rows 성공

✓ DataQualityTool: 정상 작동
  - 데이터 커버리지: 100%
  - 품질 상태: 정상

✓ N8nWebhookTool: 정상 작동
  - Webhook 호출: HTTP 200 성공
```

---

### 2. n8n Docker 환경 재점검 ✅

#### PostgreSQL 연동 확인
- n8n과 PostgreSQL 간 Docker 네트워크 통신 검증
- 컨테이너 이름 기반 연결 (`investment_postgres`)
- Health check 정상 작동

#### 로그 테이블 생성
`data_collection_logs` 테이블 추가:

```sql
CREATE TABLE data_collection_logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    market VARCHAR(10),
    limit_count INT,
    days INT,
    status VARCHAR(20),
    report TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Webhook 엔드포인트 설정
- URL: `http://localhost:5678/webhook/crew-webhook`
- Method: POST
- Status: 정상 작동 (200 OK)

---

### 3. 데이터 수집 자동화 워크플로 구축 ✅

#### n8n 워크플로 설계
[n8n_workflows/data_collection_workflow.json](n8n_workflows/data_collection_workflow.json) 작성:

**워크플로 구조:**
```
[Schedule Trigger]  →  [Execute Command]  →  [IF]  →  [Slack/Log]
  (매일 18시)          (CrewAI 실행)      (성공?)    (알림)
                                                ↓
                                          [PostgreSQL]
                                           (로그 저장)
```

**주요 노드:**
1. Schedule Trigger: 매일 18시 자동 실행
2. Webhook: 수동/외부 트리거
3. Execute Command: Python 스크립트 실행
4. IF 조건: 성공/실패 분기
5. PostgreSQL: 로그 저장
6. Slack: 결과 알림

#### 자동화 스크립트
[run_daily_collection.sh](run_daily_collection.sh) 작성:

**기능:**
- Docker 서비스 체크
- Ollama 서버 확인
- CrewAI 실행
- 로그 저장 (`logs/collection_YYYYMMDD_HHMMSS.log`)
- 결과 통계 출력

**사용법:**
```bash
./run_daily_collection.sh
```

#### 설정 가이드
[N8N_SETUP.md](N8N_SETUP.md) 작성:

- PostgreSQL Credential 설정
- Webhook 노드 구성
- 스케줄 설정 방법
- 문제 해결 가이드
- 고급 설정 (재시도, 백업 등)

---

## 생성된 파일

### 새로운 파일 (2주차)
```
ai-agent/
├── tools/                              # 커스텀 도구 모듈
│   ├── __init__.py
│   ├── data_collection_tool.py        # 데이터 수집 도구
│   ├── data_quality_tool.py           # 품질 체크 도구
│   └── n8n_webhook_tool.py            # n8n 연동 도구
├── n8n_workflows/                      # n8n 워크플로 정의
│   └── data_collection_workflow.json
├── logs/                               # 실행 로그 (자동생성)
├── investment_crew.py                  # 메인 에이전트 스크립트
├── test_tools.py                       # 도구 테스트
├── run_daily_collection.sh             # 자동화 실행 스크립트
├── requirements.txt                    # Python 의존성
├── N8N_SETUP.md                        # n8n 설정 가이드
└── WEEK2_SUMMARY.md                    # 이 문서
```

### 수정된 파일
- `.env`: 환경 변수 확인
- `docker-compose.yml`: 네트워크 설정 유지
- `init-db.sql`: 로그 테이블 추가

---

## 기술 스택 요약

### AI 프레임워크
- **CrewAI 0.80.0**: 멀티 에이전트 오케스트레이션
- **LangChain 0.3.13**: LLM 통합
- **Ollama**: 로컬 LLM 추론 (llama3.1:8b)

### 데이터 파이프라인
- **FinanceDataReader 0.9.96**: 한국 주식 데이터
- **PostgreSQL 15**: 데이터 저장소
- **psycopg2**: Python-PostgreSQL 연결

### 자동화
- **n8n**: 워크플로 자동화 플랫폼
- **Docker Compose**: 컨테이너 오케스트레이션
- **Bash Script**: 일간 수집 스크립트

---

## 실행 방법

### 1. 서비스 시작
```bash
# Docker 컨테이너 시작
docker-compose up -d

# 상태 확인
docker ps
```

### 2. 수동 실행 (테스트)
```bash
# 가상환경 활성화
source .venv/bin/activate

# CrewAI 직접 실행
python investment_crew.py

# 또는 자동화 스크립트 실행
./run_daily_collection.sh
```

### 3. n8n 워크플로 설정
```bash
# 브라우저에서 접속
open http://localhost:5678

# N8N_SETUP.md 가이드 참조
```

### 4. 자동화 활성화
n8n에서 워크플로 활성화 후 매일 18시 자동 실행

---

## 성과 지표

### 데이터 수집
- ✅ 코스피 50개 종목 수집 (테스트)
- ✅ 최근 30일 가격 데이터: 750 rows
- ✅ 수집 성공률: 100%
- ✅ 평균 수집 시간: 약 2분

### 데이터 품질
- ✅ 커버리지: 100% (50/50 종목)
- ✅ 비정상 데이터: 0건
- ✅ 결측치: 0건

### 자동화
- ✅ n8n Webhook 연동: 정상
- ✅ PostgreSQL 로그: 정상
- ✅ 스케줄 트리거: 설정 완료

---

## 다음 단계 (3주차)

[investment_agent.md](investment_agent.md)의 Phase 2 작업:

### Week 3-4: 분석 도구 개발
1. **재무 지표 계산 모듈**
   - PER, PBR, ROE, ROA 계산
   - 팩터 스코어링 로직
   - CrewAI Tool 래퍼

2. **기술적 지표 모듈**
   - TA-Lib 연동
   - 이동평균, RSI, MACD
   - 시그널 생성

3. **Screening Analyst 에이전트**
   - 팩터 기반 종목 필터링
   - 상위 20개 추출
   - 근거 설명 생성

---

## 문제 및 해결

### 이슈 1: Ollama 연결 실패
**원인:** Ollama 서버가 실행 중이 아님
**해결:** `ollama serve` 실행 또는 시스템 자동 시작 설정

### 이슈 2: n8n Webhook 타임아웃
**원인:** CrewAI 실행 시간이 15초 초과
**해결:** Webhook timeout 설정 60초로 증가

### 이슈 3: Docker 네트워크 통신
**원인:** 컨테이너 간 이름 해석 실패
**해결:** `investment_network` 생성 및 컨테이너 연결 확인

---

## 참고 자료

### 프로젝트 문서
- [README.md](README.md) - 프로젝트 개요
- [CLAUDE.md](CLAUDE.md) - Claude Code 가이드
- [investment_agent.md](investment_agent.md) - 전체 계획
- [N8N_SETUP.md](N8N_SETUP.md) - n8n 설정 가이드

### 외부 문서
- [CrewAI Documentation](https://docs.crewai.com/)
- [n8n Documentation](https://docs.n8n.io/)
- [FinanceDataReader GitHub](https://github.com/FinanceData/FinanceDataReader)

---

## 팀 노트

### 배운 점
1. CrewAI의 Tool 시스템이 매우 유연함
2. n8n과 PostgreSQL 통합이 간단함
3. Docker 네트워크로 컨테이너 간 통신이 쉬움

### 개선 필요
1. LLM 응답 속도 최적화 (현재 2-3분)
2. 에러 핸들링 강화
3. 로그 포맷 표준화

### 다음 우선순위
1. 재무 지표 계산 모듈 개발
2. Screening Analyst 구현
3. 백테스팅 프레임워크 설계

---

**작성일:** 2025-10-12
**버전:** 1.0
**작성자:** AI Agent Development Team
