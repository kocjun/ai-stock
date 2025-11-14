# 매일 아침 시장 뉴스 분석 이메일 시스템

## 개요

**오전 9시 증시 오픈 30분 전**, AI가 글로벌/국내 시장 뉴스를 분석하고 한국 투자자 관점의 요약을 이메일로 자동 발송하는 시스템입니다.

```
📰 뉴스 소스 수집 (7:00)
    ↓
🤖 AI 에이전트 분석 (7:00-7:30)
    ├─ 글로벌 시장 분석
    ├─ 반도체 뉴스 분석
    ├─ 지정학적 리스크 분석
    └─ 국내 뉴스 분석
    ↓
📧 SMTP 이메일 발송 (7:30-7:45)
    └─ Gmail SMTP를 통한 직접 발송 (N8N 독립)
    ↓
🎯 사용자 받은편지함 (오전 8시 전)
```

## 뉴스 카테고리

### 1️⃣ **글로벌 시장 (나스닥)**
- 미국 Fed 금리 결정
- S&P 500, Nasdaq 지표 변동
- 실리콘밸리 기업 뉴스
- **영향**: 달러 강세, 수출주, 금리민감주

### 2️⃣ **반도체 뉴스**
- Samsung, SK Hynix 뉴스
- TSMC 파운드리 동향
- 메모리 칩 시장 상황
- **영향**: 반도체주, 공급망 관련주

### 3️⃣ **지정학적 리스크**
- 미중 기술 갈등
- 한반도 관련 뉴스
- 러시아-우크라이나 분쟁
- **영향**: 방위사업주, 수출주, 에너지

### 4️⃣ **국내 뉴스**
- 한은 금리 결정
- 원/달러 환율 변동
- 코스피 지수 선물
- **영향**: 금리민감주, 수출주, 전반적 시장

## 시스템 아키텍처

### 1단계: News Gathering Agent
```python
도구:
- fetch_global_news()      → 나스닥, Fed 뉴스
- fetch_semiconductor_news() → 반도체 뉴스
- fetch_geopolitical_news()  → 지정학 뉴스
- fetch_korea_market_news()  → 국내 뉴스

출력:
- 분류된 뉴스 목록 (JSON)
- 카테고리별 정렬
- 영향도 초기 평가
```

### 2단계: News Analysis Agent
```python
분석 항목:
- 코스피 영향도 평가
- 영향받을 섹터 (반도체, 금융, 자동차 등)
- 영향받을 개별 종목
- 영향도 레벨 (높음/중간/낮음)
- 투자자 액션 제안

출력:
- 상세 분석 리포트
```

### 3단계: News Summarizer Agent
```python
최종 리포트:
1. 한 문장 요약
2. 카테고리별 정렬
3. 각 뉴스별:
   - 설명 (간단, 명확)
   - 영향받을 종목
   - 추천 액션
4. 종합 평가 (호재/악재)

특징:
- 한국어로 명확하게
- 기술용어 최소화
- 이해하기 쉬운 표현
```

## 파일 구조

```
core/agents/
└─ market_news_crew.py                    # AI 뉴스 분석 + 자동 SMTP 발송

core/utils/
├─ market_news_email_template.py          # HTML 이메일 템플릿
└─ market_news_sender.py                  # SMTP 직접 발송 + N8N 폴백

scripts/
└─ send_market_news.sh                    # 실행 쉘 스크립트

docs/
├─ MARKET_NEWS_SETUP.md                   # 본 문서
├─ MARKET_NEWS_SMTP_FIX.md                # SMTP 구현 상세
└─ MARKET_NEWS_SYSTEM_SUMMARY.md          # 시스템 개요

n8n_workflows/
├─ market_news_workflow.json              # N8N 스케줄 (선택사항)
└─ market_news_webhook.json               # N8N 웹훅 (선택사항)
```

## 빠른 시작 (5분)

### 1단계: SMTP 환경 변수 설정 ⭐ **필수**

Gmail 이메일로 뉴스를 발송합니다. Gmail 2FA 활성화 필수:

```bash
# Google 계정 → 보안 → 2단계 인증 → App 비밀번호 생성
# Gmail 앱에서 16자리 비밀번호 생성

export SMTP_SERVER="smtp.gmail.com"
export SMTP_PORT="587"
export SMTP_PASSWORD="생성된_앱_비밀번호"        # 예: qhir ehsr izqx lmzx
export EMAIL_FROM="your-email@gmail.com"
export REPORT_EMAIL_RECIPIENT="recipient@example.com"
```

### 2단계: 수동 테스트

```bash
cd /Users/yeongchang.jeon/workspace/ai-agent
bash scripts/send_market_news.sh
```

예상 출력:
```
✅ 가상환경 확인됨
✅ SMTP_SERVER 설정됨: smtp.gmail.com
✅ 발송자 이메일 설정됨
✅ 수신자 이메일 설정됨
✅ SMTP_PASSWORD 설정됨
✅ 뉴스 분석 및 이메일 발송 완료
```

이메일이 수신자에게 도착합니다! ✅

### 3단계: Crontab 자동화

오전 7시에 뉴스 분석을 시작하려면:

```bash
# crontab -e
# 평일 오전 7시마다 실행
0 7 * * 1-5 cd /Users/yeongchang.jeon/workspace/ai-agent && \
    bash scripts/send_market_news.sh >> logs/market_news.log 2>&1
```

## 스크립트 실행

### 수동 실행

```bash
# 단일 분석 실행
cd /path/to/ai-agent
source .venv/bin/activate

# Market News Crew만 실행
python core/agents/market_news_crew.py

# 이메일까지 발송 (N8N 웹훅 필요)
bash scripts/send_market_news.sh
```

### N8N 스케줄 실행

```
매일 평일 오전 7시 자동 실행:
- Python 스크립트 실행
- 뉴스 분석 (약 30분)
- 성공 알림 발송 (Slack, HTTP)
```

## 이메일 양식 상세

### HTML 디자인

```
┌─────────────────────────────────┐
│ 📰 오늘의 시장 뉴스              │
│ 2025년 11월 01일 (금요일)       │
│ 증시 오픈 30분 전 분석          │
└─────────────────────────────────┘

┌─────────────────────────────────┐
│ 📋 분석 리포트                   │
│                                 │
│ 🌍 글로벨 시장 (나스닥)         │
│ ⚠️  높은 영향도                │
│ - Fed 금리 인상 신호            │
│ - S&P 500 신고가                │
│                                 │
│ 🔧 반도체 뉴스                  │
│ ⚠️  높은 영향도                │
│ - Samsung 3nm 공정 진전        │
│ - TSMC 파운드리 호황            │
│                                 │
│ ⚔️ 지정학적 리스크              │
│ ⚠️  높은 영향도                │
│ - 미중 기술 제재 심화           │
│                                 │
│ 🇰🇷 국내 뉴스                  │
│ ⚠️  높은 영향도                │
│ - 한은 금리 결정 예정           │
│ - 원/달러 환율 상승             │
│                                 │
│ 📈 종합 평가                    │
│ 호재 > 악재 (긍정 신호 강화)    │
└─────────────────────────────────┘
```

### 영향도 표시

- **⚠️ 높은 영향도** (빨강): 즉시 주목 필요
- **🟡 중간 영향도** (주황): 모니터링 권장
- **🟢 낮은 영향도** (초록): 참고 수준

### 모바일 반응형

- 📱 **480px 이하** (스마트폰): 1열 레이아웃, 최소 패딩
- 📱 **768px 이하** (태블릿): 2열 레이아웃
- 💻 **1024px 이상** (데스크톱): 최대 너비 900px

## AI 에이전트 역할 상세

### News Gatherer Agent

**역할**: 전 세계 금융 시장을 모니터링하는 프로 뉴스 수집가

**목표**: 한국 코스피에 영향을 줄 글로벌/국내 뉴스를 수집하고 분류

**특징**:
- 다양한 뉴스 소스에서 실시간 정보 수집
- 자동 카테고리 분류
- 중복 뉴스 제거
- 초기 영향도 평가

### News Analyzer Agent

**역할**: 20년 경력의 금융 애널리스트

**목표**: 수집된 뉴스의 코스피 영향도를 분석하고 실행 가능한 인사이트 제공

**전문**:
- 나스닥 변동이 반도체주에 미치는 영향
- 지정학적 리스크가 방위사업주에 미치는 영향
- 글로벌 뉴스의 한국 증시 파급 효과

### News Summarizer Agent

**역할**: 금융 저널리스트

**목표**: 복잡한 금융 뉴스를 한국 투자자가 쉽게 이해할 수 있도록 요약

**특징**:
- 복잡한 경제 이론을 일반인도 이해할 수 있게 설명
- 명확하고 간결한 한국어 표현
- 실행 가능한 수준의 인사이트 제공
- 항상 한국 투자자 관점에서 재평가

## 뉴스 소스 (확장 가능)

### 현재 구현 (Mock 데이터)

```python
# 실제 구현에서는 다음을 대체:
- fetch_global_news()         → NewsAPI.org, Finnhub API
- fetch_semiconductor_news()  → 전자신문, DigiTimes, Reuters
- fetch_geopolitical_news()   → BBC, Reuters, 관련 매체
- fetch_korea_market_news()   → 연합뉴스, 매일경제, 마켓뉴스
```

### 권장 API

- **NewsAPI.org**: 글로벌 뉴스 (무료/유료)
- **Finnhub**: 금융 뉴스 (무료)
- **Polygon.io**: 미국 증시 뉴스 (유료)
- **Yahoo Finance**: 시장 데이터 (무료)

### Web Scraping (공개 소스)

- 연합뉴스 금융 (금리, 환율)
- 뉴스1 경제섹션
- 전자신문 반도체
- TechCrunch (반도체 기술)

### RSS Feed

- Bloomberg
- CNBC
- MarketWatch
- TradingView

## 문제 해결

### 뉴스 분석이 안 될 때

```bash
# 1. 로그 확인
tail -50 logs/market_news_*.log

# 2. 패키지 확인
pip install crewai crewai-tools beautifulsoup4 requests

# 3. API 키 확인 (필요시)
echo $OPENAI_API_KEY
```

### 이메일이 안 올 때

```bash
# 1. N8N 웹훅 확인
echo $N8N_WEBHOOK_URL

# 2. N8N 대시보드의 Executions 확인

# 3. N8N 로그 확인
docker logs n8n
```

## 커스터마이징

### 분석 시간 변경

`n8n_workflows/market_news_workflow.json` 수정:

```json
"expression": "0 7 * * 1-5"  // 현재: 평일 오전 7시
"expression": "0 6 * * 1-5"  // 변경: 평일 오전 6시
"expression": "30 8 * * 1-5" // 변경: 평일 오전 8시 30분
```

### 뉴스 카테고리 추가

`core/agents/market_news_crew.py` 수정:

```python
@tool
def fetch_energy_news() -> str:
    """에너지 뉴스 수집"""
    # 유가, OPEC 관련 뉴스

@tool
def fetch_forex_news() -> str:
    """환율 뉴스 수집"""
    # 환율, 국제 금융 뉴스
```

### 이메일 수신자 변경

```bash
# 여러 명에게 발송 (쉼표로 분리)
export REPORT_EMAIL_RECIPIENT="email1@example.com,email2@example.com"
```

## 자동화 플로우

### 매일 자동 실행

```
1️⃣ 오전 7:00 - N8N 스케줄 트리거
2️⃣ 오전 7:00-7:30 - Python 분석 실행
3️⃣ 오전 7:30-8:30 - AI 에이전트 처리
4️⃣ 오전 8:30 - N8N 웹훅 이메일 발송
5️⃣ 오전 8:45 - 사용자 이메일함 도착
6️⃣ 오전 9:00 - 증시 오픈 (투자자가 미리 정보 파악)
```

## 주의사항

### API 요금

- NewsAPI: 월 1,500 요청 무료, 초과 시 요금
- Finnhub: 무료 (분당 60 요청 제한)
- 기타: 확인 필요

### 성능

- 뉴스 분석에 5-30분 소요 (AI 크기에 따라)
- 네트워크 상태에 따라 변동
- 대량 뉴스 수집 시 시간 증가

### 정확도

- AI 모델의 분석 정확도에 의존
- 언어 이해도 (한영 혼용 가능)
- 실시간 뉴스 반영도에 제한

## 예시 이메일

```
📰 오늘의 시장 뉴스 - 2025년 11월 01일

🌍 글로벌 시장 (나스닥)
⚠️ Fed 금리 인상 신호
  → 달러 강세로 수출주 약세 우려
  → 영향 종목: 삼성, 현대차, SK 하이닉스

🔧 반도체 뉴스
⚠️ Samsung 3nm 공정 시작
  → 반도체 경기 회복 신호
  → 영향 종목: 삼성전자, SK Hynix

📈 종합 평가: 호재 > 악재
반도체 섹터의 구조적 호재가 금리 우려를 상쇄할 것으로 판단됩니다.
```

## 다음 단계

1. ✅ **구현 완료**: Market News Crew + Email Template + Shell Script
2. ⏳ **배포 예정**: N8N 워크플로우 임포트 및 활성화
3. ⏳ **테스트**: 실제 뉴스 소스 연동 테스트
4. ⏳ **운영**: 매일 오전 9시 자동 발송 시작

## 참고 문서

- [CrewAI 공식 문서](https://docs.crewai.com/)
- [N8N 워크플로우 가이드](https://docs.n8n.io/)
- [NewsAPI 문서](https://newsapi.org/docs)
