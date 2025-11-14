# 한국 주식시장 AI 투자 분석 에이전트 - 프로토타입 개발 계획

## 프로젝트 목표

코스피 상장사의 재무 데이터와 시장 정보를 분석하여 투자 참고 정보를 제공하는 AI 에이전트 시스템 구축

### 핵심 기능
- 공개 데이터 기반 종목 스크리닝 및 팩터 분석
- 재무 지표 자동 계산 및 시각화
- 뉴스/공시 요약 및 감성 분석
- 리스크 지표 계산 및 알림
- 투자 참고 리포트 자동 생성

### 명확한 제약사항
- **투자 권유 금지**: 모든 결과는 "참고 정보"이며 투자 판단은 사용자 책임
- **자동 매매 제한**: 매수/매도 실행은 반드시 사람이 승인
- **면책**: 모든 리포트에 데이터 출처와 면책 조항 명시

## 기술 스택

### 핵심 컴포넌트
- **CrewAI**: 멀티 에이전트 오케스트레이션
- **Ollama**: 로컬 LLM (llama3.1:8b 최소, qwen2.5:14b 권장)
- **n8n**: 워크플로 자동화 및 스케줄링
- **PostgreSQL**: 데이터 저장 (MySQL 지원 중단 예정으로 PostgreSQL 우선)
- **Python 분석 라이브러리**: pandas, numpy, scipy, TA-Lib

### 시스템 요구사항
- **CPU**: Apple Silicon M4 Max 이상 (또는 Intel/AMD 8코어 이상)
- **메모리**: 최소 16GB (8b 모델), 권장 32GB (14b 모델)
- **저장공간**: 최소 20GB (모델 10GB + 데이터 10GB)
- **OS**: macOS Sequoia 이상 또는 Ubuntu 22.04+

## 데이터 파이프라인

### Phase 1: MVP (무료/공개 데이터)

**재무 데이터**
- **FinanceDataReader**: 한국 주식 가격, 기본 재무제표
  - 설치: `pip install finance-datareader`
  - 시가총액, PER, PBR, EPS, ROE 등
  - 일간/주간/월간 가격 데이터

**시장 데이터**
- **KRX 공개 데이터**: 시장 지수, 섹터별 지수
- **한국은행 경제통계**: 금리, 환율 (API 무료)

**공시 정보**
- **DART OpenAPI**: 주요 공시 메타데이터만 (전문 제외)
  - 인증키 발급: https://opendart.fss.or.kr/
  - 사업보고서, 분기보고서 제출 여부
  - 주요 공시 발생 알림

**뉴스 데이터**
- **RSS 피드**: 네이버 금융, 연합인포맥스 등 무료 RSS
- **제한적 수집**: 법적 리스크 최소화

### Phase 2: 확장 (예산 확보 후)
- 증권사 리서치 리포트 (PDF 수집 및 파싱)
- 유료 데이터 제공업체 API (FnGuide, WISEfn 등)
- 실시간 호가/체결 데이터

### 데이터 저장 구조

```sql
-- PostgreSQL 스키마 예시
CREATE TABLE stocks (
    code VARCHAR(10) PRIMARY KEY,
    name VARCHAR(100),
    market VARCHAR(10),
    sector VARCHAR(50),
    updated_at TIMESTAMP
);

CREATE TABLE prices (
    code VARCHAR(10),
    date DATE,
    open DECIMAL(10,2),
    high DECIMAL(10,2),
    low DECIMAL(10,2),
    close DECIMAL(10,2),
    volume BIGINT,
    PRIMARY KEY (code, date)
);

CREATE TABLE financials (
    code VARCHAR(10),
    year INT,
    quarter INT,
    revenue BIGINT,
    operating_profit BIGINT,
    net_profit BIGINT,
    total_assets BIGINT,
    total_equity BIGINT,
    PRIMARY KEY (code, year, quarter)
);

CREATE TABLE news_summary (
    id SERIAL PRIMARY KEY,
    code VARCHAR(10),
    title TEXT,
    summary TEXT,
    sentiment FLOAT,
    published_at TIMESTAMP,
    source VARCHAR(100)
);
```

## AI 아키텍처: 하이브리드 접근

### LLM의 역할 (제한적)
1. **텍스트 처리**
   - 뉴스 요약 (긴 기사 → 3-5줄 요약)
   - 공시 텍스트 요약
   - 감성 분석 (긍정/중립/부정)

2. **자연어 인터페이스**
   - 사용자 질의 해석 ("삼성전자와 비슷한 종목 찾아줘")
   - 분석 결과를 자연스러운 한국어로 설명

3. **보고서 생성**
   - 분석 결과를 구조화된 리포트로 작성
   - 차트 및 표를 설명하는 텍스트 생성

### Python 분석 도구의 역할 (핵심)

```python
# 재무 지표 계산
import pandas as pd
import numpy as np

def calculate_financial_metrics(df):
    """전통적인 방식으로 정확한 재무 지표 계산"""
    df['PER'] = df['market_cap'] / df['net_profit']
    df['PBR'] = df['market_cap'] / df['total_equity']
    df['ROE'] = (df['net_profit'] / df['total_equity']) * 100
    df['ROA'] = (df['net_profit'] / df['total_assets']) * 100
    df['debt_ratio'] = (df['total_debt'] / df['total_equity']) * 100
    return df

# 팩터 스코어링
def calculate_factor_score(row):
    """복합 팩터 점수 계산"""
    score = 0
    # 밸류 팩터
    if row['PER'] > 0 and row['PER'] < 10: score += 2
    if row['PBR'] > 0 and row['PBR'] < 1: score += 2
    # 성장 팩터
    if row['revenue_growth'] > 10: score += 2
    if row['profit_growth'] > 15: score += 2
    # 수익성 팩터
    if row['ROE'] > 12: score += 1
    if row['operating_margin'] > 10: score += 1
    return score

# 기술적 지표
import talib as ta

def calculate_technical_indicators(df):
    """기술적 분석 지표 계산"""
    df['SMA_20'] = ta.SMA(df['close'], timeperiod=20)
    df['SMA_60'] = ta.SMA(df['close'], timeperiod=60)
    df['RSI'] = ta.RSI(df['close'], timeperiod=14)
    df['MACD'], df['MACD_signal'], _ = ta.MACD(df['close'])
    return df
```

### CrewAI Tool 연동

```python
from crewai.tools import BaseTool
import pandas as pd

class FinancialAnalysisTool(BaseTool):
    name: str = "financial_analyzer"
    description: str = "재무 지표를 계산하고 팩터 스코어를 산출합니다."

    def _run(self, stock_code: str) -> str:
        # PostgreSQL에서 데이터 로드
        df = load_financial_data(stock_code)

        # Python으로 정확한 계산
        metrics = calculate_financial_metrics(df)
        score = calculate_factor_score(metrics.iloc[-1])

        # 결과를 JSON으로 반환
        return {
            "code": stock_code,
            "PER": float(metrics['PER'].iloc[-1]),
            "PBR": float(metrics['PBR'].iloc[-1]),
            "ROE": float(metrics['ROE'].iloc[-1]),
            "factor_score": int(score)
        }
```

## 에이전트 역할 정의

### 1. Data Curator (데이터 수집 및 정제)
**책임**
- FinanceDataReader로 일간 가격 데이터 수집
- DART API로 공시 메타데이터 수집
- RSS 피드 파싱 및 중복 제거
- PostgreSQL에 데이터 저장

**도구**
- `DataCollectorTool`: 외부 API 호출
- `DataCleanerTool`: 이상치 제거, 결측치 처리
- `DatabaseWriterTool`: PostgreSQL INSERT/UPDATE

**출력**
- 수집된 데이터 건수 및 상태 리포트
- 데이터 품질 체크 결과

### 2. Screening Analyst (종목 스크리닝)
**책임**
- 팩터 기반 필터링 (밸류, 성장, 수익성, 모멘텀)
- 섹터별/시가총액별 상위 종목 추출
- 기술적 지표 기반 매매 시그널 감지

**도구**
- `FinancialAnalysisTool`: 재무 지표 계산
- `TechnicalAnalysisTool`: 기술적 지표 계산
- `FactorScreenerTool`: 복합 팩터 스코어링

**출력**
- 유망 종목 리스트 (상위 10-20개)
- 각 종목의 팩터 점수 및 근거

### 3. Risk Manager (리스크 분석)
**책임**
- 변동성 계산 (표준편차, 베타)
- 최대 낙폭(MDD) 분석
- 포트폴리오 집중도 체크
- 손절선 도달 감지

**도구**
- `VolatilityCalculatorTool`: 과거 변동성 분석
- `CorrelationAnalysisTool`: 종목 간 상관관계
- `RiskMetricsTool`: VaR, Sharpe Ratio (간소화)

**출력**
- 리스크 점수 (0-10)
- 경고 알림 (고위험 종목, 과도한 집중 등)

### 4. Portfolio Planner (포트폴리오 구성)
**책임**
- 추천 종목 기반 포트폴리오 제안
- 섹터 분산 최적화
- 리밸런싱 규칙 제안

**도구**
- `PortfolioOptimizerTool`: 비중 계산 (단순 동일가중 또는 시가총액 가중)
- `DiversificationCheckerTool`: 섹터/업종 분산도 확인

**출력**
- 추천 포트폴리오 (종목 + 비중)
- 예상 리스크/리턴 (과거 데이터 기반)

### 5. Alert Manager (알림 관리)
**책임**
- 급격한 가격 변동 감지 (±5% 이상)
- 주요 공시 발생 알림
- 손절선/목표가 도달 알림
- 포트폴리오 이탈 경고

**도구**
- `PriceMonitorTool`: 실시간 가격 체크
- `DisclosureMonitorTool`: DART 공시 체크
- `NotificationTool`: Slack/이메일 알림 전송

**출력**
- 실시간 알림 메시지
- 일간 알림 요약 리포트

## 워크플로 & 자동화

### n8n 스케줄 설정

```yaml
# n8n 워크플로 예시
workflows:
  - name: "일간 데이터 수집"
    trigger: "Cron (매일 18:00)"
    steps:
      - HTTP Request → CrewAI API (Data Curator 실행)
      - Webhook 수신 → PostgreSQL 저장 확인
      - Slack 알림 (성공/실패)

  - name: "주간 스크리닝 분석"
    trigger: "Cron (매주 토요일 09:00)"
    steps:
      - CrewAI 워크플로 실행 (Screening Analyst + Risk Manager)
      - 결과 수신 → Notion 페이지 생성
      - 이메일 리포트 전송

  - name: "실시간 알림"
    trigger: "Webhook (가격 급락 감지)"
    steps:
      - Alert Manager 실행
      - 조건 확인 → Slack 긴급 알림
```

### CrewAI 워크플로 통합

```python
# crew.py 확장 예시
def build_investment_crew():
    llm = build_llm()

    # 도구 초기화
    financial_tool = FinancialAnalysisTool()
    technical_tool = TechnicalAnalysisTool()
    risk_tool = RiskMetricsTool()

    # 에이전트 정의
    data_curator = Agent(
        role="Data Curator",
        goal="최신 시장 데이터를 수집하고 정제합니다",
        backstory="금융 데이터 엔지니어로 10년 경력",
        llm=llm,
        tools=[DataCollectorTool(), DataCleanerTool()]
    )

    screening_analyst = Agent(
        role="Screening Analyst",
        goal="팩터 기반으로 유망 종목을 추출합니다",
        backstory="퀀트 애널리스트로 팩터 투자 전문가",
        llm=llm,
        tools=[financial_tool, technical_tool]
    )

    risk_manager = Agent(
        role="Risk Manager",
        goal="포트폴리오 리스크를 평가하고 경고합니다",
        backstory="리스크 관리 전문가로 15년 경력",
        llm=llm,
        tools=[risk_tool]
    )

    # 태스크 정의
    data_collection = Task(
        description="코스피200 종목의 최신 가격 및 재무 데이터를 수집하세요",
        expected_output="수집된 종목 수와 데이터 품질 리포트",
        agent=data_curator
    )

    screening = Task(
        description="밸류 + 성장 팩터로 상위 20개 종목을 추출하세요",
        expected_output="추천 종목 리스트와 각 종목의 팩터 점수",
        agent=screening_analyst,
        context=[data_collection]
    )

    risk_analysis = Task(
        description="추천 종목의 리스크를 분석하고 경고사항을 도출하세요",
        expected_output="리스크 점수와 경고 메시지",
        agent=risk_manager,
        context=[screening]
    )

    crew = Crew(
        agents=[data_curator, screening_analyst, risk_manager],
        tasks=[data_collection, screening, risk_analysis],
        process=Process.sequential
    )

    return crew
```

## 리스크 관리 및 검증

### 간소화된 리스크 지표

```python
import numpy as np

def calculate_basic_risk_metrics(returns):
    """실용적인 리스크 지표 계산"""

    # 1. 변동성 (연율화)
    volatility = returns.std() * np.sqrt(252)

    # 2. 최대 낙폭 (MDD)
    cumulative = (1 + returns).cumprod()
    running_max = cumulative.expanding().max()
    drawdown = (cumulative - running_max) / running_max
    max_drawdown = drawdown.min()

    # 3. Sharpe Ratio (무위험 수익률 2% 가정)
    excess_return = returns.mean() * 252 - 0.02
    sharpe_ratio = excess_return / volatility if volatility > 0 else 0

    # 4. Win Rate
    win_rate = (returns > 0).sum() / len(returns)

    return {
        "volatility": volatility,
        "max_drawdown": max_drawdown,
        "sharpe_ratio": sharpe_ratio,
        "win_rate": win_rate
    }
```

### 백테스팅 프레임워크

```python
import backtrader as bt

class SimpleFactorStrategy(bt.Strategy):
    """팩터 기반 단순 전략"""

    def __init__(self):
        self.rebalance_days = 0

    def next(self):
        # 월간 리밸런싱
        self.rebalance_days += 1
        if self.rebalance_days % 20 != 0:
            return

        # 팩터 점수 기반 종목 선택
        stocks = self.get_top_stocks_by_factor()

        # 기존 포지션 정리
        for pos in self.positions:
            if pos not in stocks:
                self.close(data=pos)

        # 신규 포지션 진입 (동일 가중)
        target_value = self.broker.getvalue() / len(stocks)
        for stock in stocks:
            self.order_target_value(data=stock, target=target_value)

# 백테스트 실행
cerebro = bt.Cerebro()
cerebro.addstrategy(SimpleFactorStrategy)
# 데이터 추가 및 실행...
```

### 페이퍼 트레이딩 단계

1. **Phase 1 (1-2개월)**: 과거 데이터로 백테스팅
2. **Phase 2 (3-6개월)**: 실시간 데이터로 페이퍼 트레이딩
3. **Phase 3 (검증 후)**: 소액 실전 투자 (100-500만원)

## 구현 로드맵

### Phase 1: 기본 인프라 (2주) ✅ **완료 (2025-10-12)**

**Week 1** ✅
- [x] PostgreSQL 설치 및 스키마 설계 (Docker 기반)
- [x] FinanceDataReader 연동 테스트 (코스피 50개 종목)
- [x] 기본 데이터 수집 스크립트 작성 (collect_data.py)

**Week 2** ✅
- [x] CrewAI 단일 에이전트 구현 (Data Curator - investment_crew.py)
- [x] n8n Docker 환경 구축 및 PostgreSQL 연동 완료
- [x] 데이터 수집 자동화 워크플로 구축 (run_daily_collection.sh)

**산출물** ✅
- PostgreSQL 데이터베이스 (종목 50개 + 가격 데이터 750 rows)
- 데이터 수집 스크립트 (collect_data.py, investment_crew.py)
- n8n 워크플로 정의 (data_collection_workflow.json)
- 커스텀 CrewAI 도구 3개 (tools/ 디렉터리)
- 자동화 실행 스크립트 (run_daily_collection.sh)
- 설정 가이드 문서 (N8N_SETUP.md, WEEK2_SUMMARY.md)

### Phase 2: 분석 도구 개발 (3주)

**Week 3-4**
- [ ] 재무 지표 계산 모듈 구현 (PER, PBR, ROE 등)
- [ ] 팩터 스코어링 로직 구현
- [ ] CrewAI Tool 래퍼 작성 (FinancialAnalysisTool)

**Week 5**
- [ ] 기술적 지표 계산 모듈 (TA-Lib 연동)
- [ ] Screening Analyst 에이전트 구현
- [ ] 단순 스크리닝 테스트 (상위 20개 종목 추출)

**산출물**
- 재무/기술적 분석 Python 모듈
- Screening Analyst 에이전트
- 스크리닝 결과 샘플 리포트

### Phase 3: 리스크 관리 및 통합 (3주)

**Week 6-7**
- [ ] 리스크 지표 계산 모듈 (변동성, MDD)
- [ ] Risk Manager 에이전트 구현
- [ ] Portfolio Planner 에이전트 구현

**Week 8**
- [ ] 전체 워크플로 통합 (Data → Screening → Risk → Portfolio)
- [ ] n8n 스케줄 설정 (주간 분석)
- [ ] 결과 리포트 생성 (Markdown/HTML)

**산출물**
- 통합 CrewAI 워크플로
- 주간 분석 리포트 자동 생성
- n8n 워크플로 3개 (수집, 분석, 알림)

### Phase 4: 검증 및 개선 (2주)

**Week 9**
- [ ] 과거 1년 데이터로 백테스팅
- [ ] 전략 성과 분석 (수익률, MDD, Sharpe)
- [ ] 개선점 도출

**Week 10**
- [ ] Alert Manager 구현 (가격 급락 알림)
- [ ] 페이퍼 트레이딩 시작
- [ ] 모니터링 대시보드 구축 (선택)

**산출물**
- 백테스트 리포트
- 페이퍼 트레이딩 로그
- 개선 계획서

### 전체 타임라인
```
Week 1-2:  [█████완료█████] ✅ Phase 1: 기본 인프라
Week 3-5:  [=========분석 도구=========] 🔄 진행 예정
Week 6-8:  [=========통합=========]
Week 9-10: [====검증====]
------------------------------------------
총 소요: 10주 (2.5개월)
현재 진행률: 20% (Week 2/10 완료)
```

### 진행 상황 업데이트

**완료일: 2025-10-12**

#### Week 1-2 주요 성과
1. **인프라 구축**
   - Docker 기반 PostgreSQL + n8n 환경 구성
   - 데이터베이스 스키마 설계 (stocks, prices, financials, news_summary, logs)
   - 네트워크 설정 및 컨테이너 통신 검증

2. **데이터 파이프라인**
   - FinanceDataReader 연동 완료
   - 코스피 50개 종목, 30일 데이터 수집 성공 (성공률 100%)
   - 데이터 품질 체크 시스템 구현

3. **AI 에이전트**
   - Data Curator 에이전트 구현 (investment_crew.py)
   - 커스텀 도구 3개 개발:
     * DataCollectionTool - 데이터 수집 자동화
     * DataQualityTool - 품질 검증
     * N8nWebhookTool - 워크플로 통합

4. **자동화**
   - n8n 워크플로 설계 및 테스트
   - 일간 자동 실행 스크립트 (run_daily_collection.sh)
   - 로그 저장 및 모니터링 체계

#### 생성된 주요 파일
- `investment_crew.py` - Data Curator 에이전트 메인
- `tools/` - 커스텀 도구 모듈 디렉터리
- `n8n_workflows/` - 워크플로 정의
- `N8N_SETUP.md` - n8n 설정 가이드
- `WEEK2_SUMMARY.md` - 2주차 완료 보고서
- `requirements.txt` - Python 의존성
- `run_daily_collection.sh` - 자동화 스크립트

#### 다음 마일스톤 (Week 3-4)
- 재무 지표 계산 모듈 개발
- 팩터 스코어링 시스템 구축
- Screening Analyst 에이전트 구현

## 법적 및 윤리적 고려사항

### 면책 조항 (모든 리포트에 포함)

```markdown
⚠️ 투자 유의사항

본 분석은 공개된 데이터를 기반으로 한 참고 정보이며,
투자 권유가 아닙니다. 모든 투자 판단과 그에 따른
손실은 투자자 본인의 책임입니다.

- 데이터 출처: FinanceDataReader, DART OpenAPI
- 분석 시점: {timestamp}
- 과거 데이터 기반 분석이므로 미래 수익을 보장하지 않습니다
```

### 데이터 사용 제한
- **저작권 준수**: 크롤링 금지, 공식 API만 사용
- **재배포 금지**: 수집한 데이터는 개인 분석 용도로만 사용
- **상업적 이용 금지**: 타인에게 유료 서비스 제공 시 별도 라이선스 필요

### 자동 매매 제한
- 매수/매도 신호는 "제안"일 뿐, 자동 실행 금지
- HTS/MTS API 연동 시 반드시 사람이 최종 승인
- 긴급 손절 알림은 제공하되 자동 실행은 금지

## 성공 지표 (KPI)

### Phase 1-2 (인프라 + 분석 도구)
- [ ] 코스피200 종목 일간 데이터 수집률 95% 이상
- [ ] 재무 지표 계산 정확도 100% (수동 검증 대비)
- [ ] 스크리닝 실행 시간 10초 이내

### Phase 3-4 (통합 + 검증)
- [ ] 백테스트 연평균 수익률 > 코스피200 지수
- [ ] 최대 낙폭 < -30%
- [ ] Sharpe Ratio > 0.5
- [ ] 페이퍼 트레이딩 3개월 수익률 > 0%

## 참고 자료

### 기술 문서
- [CrewAI 공식 문서](https://docs.crewai.com/)
- [FinanceDataReader 사용법](https://github.com/FinanceData/FinanceDataReader)
- [DART OpenAPI 가이드](https://opendart.fss.or.kr/guide/main.do)
- [backtrader 백테스팅](https://www.backtrader.com/)

### 금융 지식
- 팩터 투자 (밸류, 모멘텀, 퀄리티, 사이즈)
- 현대 포트폴리오 이론 (MPT)
- 리스크 관리 기법 (VaR, CVaR, MDD)

## 다음 단계

1. **즉시 시작**: PostgreSQL 설치 및 스키마 생성
2. **금주 내**: FinanceDataReader로 샘플 데이터 수집 테스트
3. **다음 주**: CrewAI Data Curator 에이전트 프로토타입 작성

---
*최종 수정: 2025-10-12*
*버전: 2.0 (프로토타입 개발 계획)*
