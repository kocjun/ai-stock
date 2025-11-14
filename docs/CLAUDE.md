# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 개요

한국 주식시장 투자 분석을 위한 AI 에이전트 플랫폼으로, 다음 기술들을 결합합니다:
- **CrewAI**: 역할 기반 멀티 에이전트 오케스트레이션 프레임워크
- **Ollama**: 로컬 LLM 추론 엔진 (기본 모델: llama3.1:8b)
- **n8n**: 워크플로 자동화 및 통합 플랫폼
- **PostgreSQL**: 데이터 저장소 (Docker 기반)
- **FinanceDataReader**: 한국 주식 데이터 수집

코스피 상장사의 재무제표, 시장 데이터, 뉴스를 종합 분석하여 리스크 관리 계획이 포함된 투자 참고 정보를 생성합니다.

## 프로젝트 상태

**현재 진행 상황:** Phase 1 완료 (Week 1-2) ✅
**완료일:** 2025-10-12
**다음 단계:** Phase 2 - 분석 도구 개발 (Week 3-5)

### 완료된 기능
- ✅ Docker 기반 PostgreSQL + n8n 환경 구축
- ✅ FinanceDataReader 연동 및 데이터 수집 파이프라인
- ✅ Data Curator 에이전트 구현
- ✅ 커스텀 CrewAI 도구 3개 (데이터 수집, 품질 체크, n8n 연동)
- ✅ 자동화 워크플로 및 스케줄링
- ✅ 데이터 품질 검증 시스템

## 개발 환경 설정

### 초기 환경 구성
```bash
# Python 가상환경 생성 및 활성화
python3 -m venv .venv
source .venv/bin/activate

# 의존성 설치
pip install -r requirements.txt

# Docker 서비스 시작
docker-compose up -d
```

### 필수 서비스
1. **Ollama**: 로컬 LLM 서버
   - 설치: `brew install ollama`
   - 모델 다운로드: `ollama pull llama3.1:8b`
   - 확인: `curl http://localhost:11434/api/tags`

2. **PostgreSQL**: 데이터베이스 (Docker)
   - 컨테이너: `investment_postgres`
   - 포트: `5432`
   - 접속: `docker exec -it investment_postgres psql -U invest_user -d investment_db`

3. **n8n**: 워크플로 자동화 플랫폼 (Docker)
   - 컨테이너: `n8n`
   - UI 접속: `http://localhost:5678`
   - 인증: admin / (.env에서 설정)

### 에이전트 실행
```bash
# 데이터 수집 (간단한 Python 스크립트)
python collect_data.py

# AI 에이전트 실행 (Data Curator)
python investment_crew.py

# 자동화 스크립트 (Docker + Ollama 체크 포함)
./run_daily_collection.sh
```

## 아키텍처

### 핵심 컴포넌트

**investment_crew.py** - Data Curator 에이전트 메인 스크립트
- `build_llm()`을 통해 LLM 클라이언트 초기화 (.env에서 설정 읽음)
- Data Curator 에이전트 정의 (역할: 금융 데이터 엔지니어)
- 3개 순차 태스크: 데이터 수집 → 품질 검증 → 리포트 작성
- 커스텀 도구 통합 (DataCollectionTool, DataQualityTool, N8nWebhookTool)
- 로컬 Ollama 서버를 가리키는 OpenAI 호환 API 사용

**tools/** - 커스텀 CrewAI 도구 모듈
- `data_collection_tool.py`: FinanceDataReader 연동, 종목/가격 데이터 수집
- `data_quality_tool.py`: 데이터 품질 체크, 커버리지 분석, 이상치 감지
- `n8n_webhook_tool.py`: n8n 워크플로 트리거, JSON 직렬화 및 전송

**collect_data.py** - 단순 데이터 수집 스크립트
- 에이전트 없이 직접 데이터 수집
- 빠른 테스트 및 디버깅용

**db_utils.py** - PostgreSQL 연결 유틸리티
- 데이터베이스 연결 관리
- 일괄 삽입/업데이트 함수
- 연결 테스트 및 헬퍼 함수

**환경 변수 설정** (.env)
- `OPENAI_API_BASE`: Ollama 엔드포인트 (기본값: http://127.0.0.1:11434)
- `OPENAI_MODEL_NAME`: 사용할 모델 (기본값: llama3.1:8b)
- `OPENAI_API_KEY`: 로컬은 "ollama", 원격 OpenAI 모델 사용 시 실제 키
- `CREWAI_LLM_PROVIDER`: 로컬 추론 시 "ollama"로 설정
- `N8N_WEBHOOK_URL`: 결과 전달을 위한 웹훅 엔드포인트
- `CREWAI_STORAGE_DIR`: 태스크 출력 및 상태 저장 디렉터리 (.crewai/)
- `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`: PostgreSQL 연결 정보

**n8n 통합**
- n8n과 PostgreSQL은 Docker Compose로 함께 실행
- CrewAI는 웹훅 POST로 n8n 워크플로에 결과 전송
- n8n은 크론, 웹훅, 이벤트 트리거를 통해 CrewAI 실행 가능
- 로그는 PostgreSQL `data_collection_logs` 테이블에 저장

### 에이전트 역할

**구현 완료:**
- **Data Curator** (investment_crew.py): 데이터 수집 및 품질 검증
  - 종목 리스트 수집
  - 가격 데이터 수집
  - 데이터 품질 체크
  - 리포트 작성

**구현 예정 (investment_agent.md 기준):**
- **Screening Analyst**: 팩터 기반 종목 필터링 (Week 3-5)
- **Risk Manager**: 변동성, MDD 분석 (Week 6-8)
- **Portfolio Planner**: 자산배분 및 리밸런싱 (Week 6-8)
- **Alert Manager**: 가격 급락 알림 (Week 9-10)

### 데이터베이스 스키마

**주요 테이블:**
- `stocks`: 종목 마스터 (code, name, market, sector)
- `prices`: 일별 가격 데이터 (code, date, open, high, low, close, volume)
- `financials`: 분기별 재무제표 (code, year, quarter, revenue, profit, assets, equity, debt)
- `news_summary`: 뉴스 요약 및 감성 분석 (code, title, summary, sentiment, published_at)
- `data_collection_logs`: 수집 로그 (timestamp, market, limit, days, status, report)

**뷰:**
- `latest_financials`: 최신 재무 데이터 + 계산된 지표 (ROE, ROA, 부채비율)
- `stocks_with_latest_price`: 종목 정보 + 최근 가격

### 데이터 파이프라인
- **재무 데이터**: FinanceDataReader (한국 주식 가격, 기본 재무제표)
- **시장 지표**: KRX 지수 (계획 중)
- **공시 정보**: DART OpenAPI (계획 중)
- **뉴스**: RSS 피드 (계획 중)
- **저장소**: PostgreSQL (Docker 기반)

## 코드 패턴

### LLM 클라이언트 초기화
```python
from crewai import LLM
from dotenv import load_dotenv
import os

load_dotenv()

llm = LLM(
    model=os.getenv("OPENAI_MODEL_NAME", "llama3.1:8b"),
    base_url=os.getenv("OPENAI_API_BASE", "http://127.0.0.1:11434"),
    api_key=os.getenv("OPENAI_API_KEY", "ollama")
)
```

### 커스텀 CrewAI Tool 패턴
```python
from crewai.tools import BaseTool
from typing import Any

class CustomTool(BaseTool):
    name: str = "tool_name"
    description: str = """
    도구 설명 (다중 라인 가능)

    사용법:
    - 명령어 형식 설명
    """

    def _run(self, argument: str) -> str:
        """실제 실행 로직"""
        try:
            # 구현 내용
            result = do_something(argument)
            return f"✓ 성공: {result}"
        except Exception as e:
            return f"✗ 실패: {str(e)}"
```

### PostgreSQL 연결 패턴
```python
from db_utils import get_db_connection, insert_stocks_batch

# 연결 생성
conn = get_db_connection()
cur = conn.cursor()

# 쿼리 실행
cur.execute("SELECT * FROM stocks LIMIT 10")
results = cur.fetchall()

# 일괄 삽입
stocks_data = [
    ("005930", "삼성전자", "KOSPI", "전기전자"),
    ("000660", "SK하이닉스", "KOSPI", "전기전자")
]
insert_stocks_batch(stocks_data)

# 정리
cur.close()
conn.close()
```

### n8n Webhook 호출 패턴
```python
from tools.n8n_webhook_tool import N8nWebhookTool
import os

webhook_url = os.getenv("N8N_WEBHOOK_URL")
webhook = N8nWebhookTool(webhook_url=webhook_url)

result = webhook.run({
    "type": "data_collection_report",
    "market": "KOSPI",
    "status": "success",
    "message": "데이터 수집 완료"
})
print(result)  # ✓ n8n webhook 호출 성공 (status: 200)
```

## 테스트 및 디버깅

### 서비스 상태 확인
```bash
# Docker 컨테이너 상태
docker ps
docker-compose logs -f

# PostgreSQL 상태
docker exec investment_postgres pg_isready -U invest_user

# n8n 상태
curl -s http://localhost:5678 | head -5

# Ollama 상태
ollama ps
ollama list
curl http://localhost:11434/api/tags

# CrewAI 실행 로그
ls -l .crewai/
cat logs/collection_*.log
```

### 테스트 스크립트
```bash
# 도구 단위 테스트
python test_tools.py

# FinanceDataReader 테스트
python test_fdr.py

# 데이터베이스 연결 테스트
python db_utils.py

# 전체 에이전트 테스트
python investment_crew.py
```

### 자주 발생하는 문제

**Ollama 연결 실패**
```bash
# 문제: Connection refused to localhost:11434
# 해결: Ollama 서버 실행
ollama serve

# 확인
curl http://localhost:11434/api/tags
```

**n8n 웹훅 실패**
```bash
# 문제: n8n 연결 실패
# 해결: 컨테이너 재시작
docker-compose restart n8n

# 웹훅 수동 테스트
curl -X POST http://localhost:5678/webhook/crew-webhook \
  -H "Content-Type: application/json" \
  -d '{"type":"test","message":"hello"}'
```

**PostgreSQL 연결 실패**
```bash
# 문제: authentication failed
# 해결: .env 파일 비밀번호 확인
cat .env | grep DB_PASSWORD

# 컨테이너 내에서 직접 접속 테스트
docker exec -it investment_postgres psql -U invest_user -d investment_db
```

**모델을 찾을 수 없음**
```bash
# 문제: Model 'llama3.1:8b' not found
# 해결: 모델 다운로드
ollama pull llama3.1:8b
ollama list
```

**데이터 수집 실패**
```bash
# FinanceDataReader API 제한 확인
python test_fdr.py

# 네트워크 연결 확인
ping finance.naver.com

# 종목 코드 유효성 확인
# 005930 (삼성전자) 등 유효한 코드 사용
```

## 파일 구조

```
ai-agent/
├── investment_crew.py          # Data Curator 에이전트 메인 ⭐
├── collect_data.py             # 간단한 데이터 수집 스크립트
├── db_utils.py                 # PostgreSQL 연결 유틸리티
├── crew.py                     # CrewAI 샘플 (레퍼런스용)
│
├── tools/                      # 커스텀 도구 모듈 ⭐
│   ├── __init__.py
│   ├── data_collection_tool.py
│   ├── data_quality_tool.py
│   └── n8n_webhook_tool.py
│
├── n8n_workflows/              # n8n 워크플로 정의 ⭐
│   └── data_collection_workflow.json
│
├── run_daily_collection.sh     # 자동화 실행 스크립트 ⭐
├── test_fdr.py                 # FDR 테스트
├── test_tools.py               # 도구 테스트
│
├── docker-compose.yml          # Docker 서비스 정의
├── init-db.sql                 # PostgreSQL 스키마
├── .env                        # 환경 변수
├── requirements.txt            # Python 의존성
│
├── README.md                   # 프로젝트 개요
├── CLAUDE.md                   # 이 문서
├── N8N_SETUP.md               # n8n 설정 가이드 ⭐
├── WEEK2_SUMMARY.md            # 2주차 완료 보고서 ⭐
└── investment_agent.md         # 전체 개발 계획
```

## 중요 사항

### 개발 원칙
- 모든 에이전트 프롬프트와 출력은 기본적으로 **한국어**로 설정
- CrewAI 저장 디렉터리(.crewai/)는 태스크 상태를 포함하므로 **활성 워크플로 중에는 삭제하지 말 것**
- 시스템은 **방어적 보안 분석 용도**로 설계 - 승인 워크플로 없이 주문 실행 기능을 구현하지 말 것
- **투자 권유 금지** - 모든 결과는 "참고 정보"이며 면책 조항 필수

### 데이터 관리
- 데이터는 **개인 분석 용도로만 사용** (재배포 금지)
- 공식 API만 사용 (크롤링 금지)
- 데이터 출처를 항상 명시

### Docker 관리
- PostgreSQL과 n8n은 `investment_network`로 연결
- 컨테이너 이름으로 통신 (`investment_postgres`, `n8n`)
- 데이터는 볼륨에 저장 (`postgres-data/`, `n8n-data/`)

### 다음 개발 단계
자세한 내용은 `investment_agent.md` 참조
- Week 3-4: 재무 지표 계산 모듈, 팩터 스코어링
- Week 5: 기술적 지표, Screening Analyst 구현
- Week 6-8: Risk Manager, Portfolio Planner, 전체 통합
- Week 9-10: 백테스팅, 페이퍼 트레이딩

---

*최종 수정: 2025-10-12*
*버전: 2.0 (Phase 1 완료)*
