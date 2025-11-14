# 업종별 대장주 투자 전략 가이드

업종별 대장주에 집중 투자하는 새로운 전략을 페이퍼 트레이딩 시스템에 추가했습니다.

---

## 📋 목차

1. [전략 개요](#전략-개요)
2. [4가지 투자 전략](#4가지-투자-전략)
3. [사용 방법](#사용-방법)
4. [위험성 분석](#위험성-분석)
5. [권장 사항](#권장-사항)

---

## 전략 개요

### 선정 종목 (10개)

한국 주식시장 5개 주요 업종의 대장주 1-2개씩 선정:

| 업종 | 대장주 1순위 | 대장주 2순위 |
|------|-------------|-------------|
| **반도체/전기전자** | 삼성전자 (005930) | SK하이닉스 (000660) |
| **자동차/운수장비** | 현대차 (005380) | 기아 (000270) |
| **화학** | LG화학 (051910) | 롯데케미칼 (011170) |
| **금융** | KB금융 (105560) | 신한지주 (055550) |
| **IT/인터넷** | 네이버 (035420) | 카카오 (035720) |

### 투자 비중

- **업종당 2개 선정 시**: 각 종목 10% (총 10개)
- **업종당 1개 선정 시**: 각 종목 20% (총 5개)

---

## 4가지 투자 전략

### 1. AI 전략 (기존)

```bash
python3 paper_trading/trading_crew.py --strategy ai
```

**특징:**
- AI가 시장 전체를 분석하여 최적 종목 선정
- 재무/기술적 팩터 기반
- 동적 종목 선택 (매번 변경 가능)
- 가치주, 성장주 등 다양한 스타일

**장점:**
- 데이터 기반 객관적 선택
- 밸류에이션 고려
- 숨은 가치주 발굴 가능

**단점:**
- AI 신뢰도에 의존
- 변동성 높을 수 있음
- 종목이 자주 바뀔 수 있음

---

### 2. 업종별 대장주 전략 (기존)

```bash
python3 paper_trading/trading_crew.py --strategy sector
```

**특징:**
- 5개 업종 대장주 **고정** (하드코딩)
- 시가총액 상위 안정적 기업
- 단순하고 이해하기 쉬움
- 유동성 최상

**장점:**
- 안정성 높음
- 유동성 걱정 없음
- 정보 접근 용이
- 심리적 신뢰도 높음

**단점:**
- 분산 효과 제한적 (10개)
- 대장주 프리미엄 (고평가)
- AI 인사이트 활용 못함
- 중소형주 대비 수익률 저조 가능
- **정적 선정**: 시장 변화 반영 안됨

---

### 3. AI 기반 대장주 전략 (신규 ⭐)

```bash
python3 paper_trading/trading_crew.py --strategy ai-sector
```

**특징:**
- **동적 대장주 선정**: AI가 실시간으로 업종별 대장주 선정
- **거래량 중심** (30% 가중치): 유동성 최우선
- 다차원 분석: 거래량(30%) + 재무(30%) + 기술(20%) + 리스크(20%)
- 블랙리스트 자동 통합
- 최소 거래대금 500억원 필터

**장점:**
- ✅ 시장 변화에 적응 (동적 선정)
- ✅ 거래량 기반 안정성
- ✅ 블랙리스트 자동 필터링
- ✅ 유동성 보장 (거래대금 기준)
- ✅ 대형주 안정성 + AI 인사이트 결합

**단점:**
- 실행 시간 약간 증가 (분석 필요)
- 재무/기술/리스크 지표 아직 프로토타입

**추천 대상:**
- 안정성 + 데이터 기반 투자 원하는 투자자
- 거래량을 중시하는 투자자
- 대형주 위주 포트폴리오 선호

📖 **상세 가이드**: [AI_SECTOR_LEADER_GUIDE.md](../docs/AI_SECTOR_LEADER_GUIDE.md)

---

### 4. 하이브리드 전략 (기존)

```bash
python3 paper_trading/trading_crew.py --strategy hybrid
```

**특징:**
- 50% AI 추천 + 50% 대장주 (고정)
- AI 5개 + 대장주 5개 = 총 10개
- 안정성과 수익성 균형

**장점:**
- 두 전략의 장점 결합
- 분산 효과 향상
- 리스크 분산

**단점:**
- 실행 시간이 길어짐 (AI 분석 필요)
- 두 전략 간 중복 가능

---

## 사용 방법

### 기본 실행

```bash
# 1. 업종별 대장주 전략 (분석만)
python3 paper_trading/trading_crew.py --strategy sector

# 2. 실제 매매 실행
python3 paper_trading/trading_crew.py --strategy sector --execute

# 3. 하이브리드 전략
python3 paper_trading/trading_crew.py --strategy hybrid --execute
```

### 옵션 설정

```bash
python3 paper_trading/trading_crew.py \
    --strategy sector \
    --account-id 1 \
    --cash-reserve 0.2 \
    --stop-loss -10.0 \
    --take-profit 20.0 \
    --execute \
    --save-log
```

**주요 옵션:**
- `--strategy`: 전략 선택 (ai/sector/hybrid)
- `--account-id`: 계좌 ID (기본: 1)
- `--cash-reserve`: 현금 보유 비율 (기본: 0.2 = 20%)
- `--stop-loss`: 손절 기준 (기본: -10%)
- `--take-profit`: 익절 기준 (기본: +20%)
- `--execute`: 실제 매매 실행 (없으면 분석만)
- `--save-log`: 로그 파일 저장

### 크론잡 설정

#### 업종별 대장주 전략 자동화

`run_paper_trading.sh` 파일 수정:

```bash
#!/bin/bash

# 전략 선택
STRATEGY="sector"  # ai, sector, hybrid 중 선택

python3 paper_trading/trading_crew.py \
    --strategy $STRATEGY \
    --account-id 1 \
    --cash-reserve 0.2 \
    --stop-loss -10.0 \
    --take-profit 20.0 \
    --execute \
    --save-log
```

#### 전략 A/B 테스트

2개 계좌로 각각 다른 전략 실행:

```bash
# 계좌 1: AI 전략
python3 paper_trading/trading_crew.py --account-id 1 --strategy ai --execute

# 계좌 2: 대장주 전략
python3 paper_trading/trading_crew.py --account-id 2 --strategy sector --execute
```

---

## 위험성 분석

### 📊 종합 평가

| 항목 | AI 전략 | 업종별 대장주 | AI 기반 대장주 ⭐ | 하이브리드 |
|------|---------|---------------|------------------|-----------|
| **안정성** | ★★★☆☆ | ★★★★☆ | ★★★★★ | ★★★★☆ |
| **수익성** | ★★★★☆ | ★★★☆☆ | ★★★★☆ | ★★★★☆ |
| **분산성** | ★★★☆☆ | ★★☆☆☆ | ★★★☆☆ | ★★★☆☆ |
| **유동성** | ★★★☆☆ | ★★★★★ | ★★★★★ | ★★★★☆ |
| **단순성** | ★★☆☆☆ | ★★★★★ | ★★★★☆ | ★★★☆☆ |
| **적응력** | ★★★★☆ | ★☆☆☆☆ | ★★★★★ | ★★★☆☆ |

### 주요 위험 요소

#### 1. 집중 리스크 (위험도: 상)

**문제:**
- 5-10개 종목만으로 구성
- 개별 종목 급락 시 큰 타격

**완화 방안:**
- 업종당 2개씩 선정 (총 10개)
- 손절 기준 엄격 준수 (-7% 또는 -10%)
- 각 종목 비중 10% 이하

#### 2. 업종 상관성 (위험도: 중상)

**문제:**
- 반도체, 자동차, 화학은 경기 민감
- 동시 하락 가능성

**완화 방안:**
- 방어적 업종(금융) 비중 조정
- 경기 선행 지표 모니터링

#### 3. 대장주 프리미엄 (위험도: 중)

**문제:**
- 이미 높은 밸류에이션
- 추가 상승 여력 제한

**완화 방안:**
- PER, PBR 모니터링
- 과열 구간에서 비중 축소

#### 4. 섹터 로테이션 (위험도: 중)

**문제:**
- 시장 국면에 따라 특정 업종 소외

**예시:**
- 금리 상승기 → IT/인터넷 부진
- 경기 침체기 → 자동차, 화학 부진
- 수출 부진기 → 반도체 부진

**완화 방안:**
- 분기별 업종 로테이션 점검
- 거시경제 지표 기반 업종 교체

### 정량적 위험 지표

| 지표 | 추정치 | 비고 |
|------|--------|------|
| **연 변동성** | 20-25% | 대형주 평균 |
| **정상 MDD** | 15-20% | 일반적 조정 |
| **위기 MDD** | 30-40% | 2020 코로나, 2022 금리인상 |
| **업종 상관계수** | 0.6-0.7 | 분산 효과 제한적 |
| **샤프 비율** | 0.4-0.6 | 중간 수준 |

---

## 권장 사항

### 리스크 관리

#### 포지션 관리
```
✓ 업종당 20% 상한 (5개 업종)
✓ 종목당 15% 상한 (업종당 2개)
✓ 현금 비중 10-20% 유지
```

#### 손익 관리
```
• 개별 종목 손절: -7% (대장주는 -10% 완화 가능)
• 개별 종목 익절: +20%
• 포트폴리오 손절: 총 자산 -15%
```

#### 리밸런싱
```
• 분기별 정기 리밸런싱
• 비중 5%p 이탈 시 조정
• 업종 교체는 반기 1회 검토
```

#### 모니터링
```
일일: 개별 종목 뉴스/공시
주간: 업종별 성과 점검
월간: 거시경제 지표 분석
분기: 실적 발표 점검
```

### 적합한 투자자

**업종별 대장주 전략이 적합한 경우:**
- ✅ 주식 투자 초보자
- ✅ 안정성 우선 투자자
- ✅ 장기 투자 지향 (6개월 이상)
- ✅ 대형주 선호

**AI 전략이 적합한 경우:**
- ✅ 적극적 수익 추구
- ✅ 데이터 기반 투자 선호
- ✅ 변동성 수용 가능
- ✅ 중소형주 포함 원함

### 전략 혼합 방안

#### 옵션 1: 계좌 분할
```bash
# 계좌 1 (70%): 대장주 전략
python3 paper_trading/trading_crew.py --account-id 1 --strategy sector --execute

# 계좌 2 (30%): AI 전략
python3 paper_trading/trading_crew.py --account-id 2 --strategy ai --execute
```

#### 옵션 2: 하이브리드 사용
```bash
# 50:50 혼합
python3 paper_trading/trading_crew.py --strategy hybrid --execute
```

#### 옵션 3: 분기별 전략 교체
```
Q1-Q2: 대장주 전략 → 성과 측정
Q3-Q4: AI 전략 → 성과 비교
→ 다음 해 더 나은 전략 선택
```

---

## 위험 분석 보고서

상세한 위험성 분석 보고서를 생성하려면:

```bash
cd paper_trading
python3 sector_leader_strategy.py --action risk --save-report
```

생성된 보고서 위치:
```
paper_trading/reports/sector_leader_risk_analysis_YYYYMMDD_HHMMSS.md
```

---

## 실전 예시

### 시나리오 1: 초보 투자자 (안정성 우선)

```bash
# 업종별 대장주 전략 선택
# 손절 -7%로 엄격하게
# 현금 30% 보유로 보수적 운용

python3 paper_trading/trading_crew.py \
    --strategy sector \
    --cash-reserve 0.3 \
    --stop-loss -7.0 \
    --take-profit 15.0 \
    --execute
```

### 시나리오 2: 공격적 투자자 (수익성 우선)

```bash
# AI 전략 선택
# 현금 10% 최소화
# 손절 -15%로 여유 있게

python3 paper_trading/trading_crew.py \
    --strategy ai \
    --limit 30 \
    --top-n 15 \
    --cash-reserve 0.1 \
    --stop-loss -15.0 \
    --take-profit 30.0 \
    --execute
```

### 시나리오 3: 균형 투자자

```bash
# 하이브리드 전략
# 중도적 리스크 관리

python3 paper_trading/trading_crew.py \
    --strategy hybrid \
    --limit 20 \
    --top-n 10 \
    --cash-reserve 0.2 \
    --stop-loss -10.0 \
    --take-profit 20.0 \
    --execute
```

---

## FAQ

### Q1. 어떤 전략이 가장 좋나요?

**A**: 투자 성향에 따라 다릅니다.
- 안정성 우선 → **업종별 대장주**
- 수익성 우선 → **AI 전략**
- 균형 → **하이브리드**

최소 3-6개월 실행 후 결과를 비교해보세요.

### Q2. 대장주 종목을 바꿀 수 있나요?

**A**: 가능합니다. `sector_leader_strategy.py` 파일의 `SECTOR_LEADERS` 딕셔너리를 수정하세요.

```python
SECTOR_LEADERS = {
    "반도체/전기전자": {
        "leaders": [
            {"code": "005930", "name": "삼성전자", "priority": 1},
            {"code": "000660", "name": "SK하이닉스", "priority": 2}
        ]
    },
    # ... 추가/수정 가능
}
```

### Q3. 업종을 3개만 선택할 수 있나요?

**A**: 가능합니다.

```bash
python3 paper_trading/sector_leader_strategy.py \
    --action recommend \
    --num-sectors 3 \
    --leaders-per-sector 2
```

### Q4. 두 전략을 동시에 비교하려면?

**A**: 2개의 가상 계좌를 만들어 각각 다른 전략을 실행하세요.

```bash
# 1. 계좌 2 생성
python3 paper_trading/setup_schema.py --create-account

# 2. 각각 실행
python3 paper_trading/trading_crew.py --account-id 1 --strategy ai --execute
python3 paper_trading/trading_crew.py --account-id 2 --strategy sector --execute

# 3. 성과 비교
python3 paper_trading/portfolio_manager.py metrics --account-id 1
python3 paper_trading/portfolio_manager.py metrics --account-id 2
```

### Q5. 대장주 전략이 AI보다 안전한가요?

**A**: 일반적으로 그렇습니다.
- 대형주는 변동성이 낮음
- 유동성 높아 손절 용이
- 재무구조 견고

하지만 "안전 ≠ 수익성"입니다. 시장 상황에 따라 AI 전략이 더 나을 수 있습니다.

---

## 결론

업종별 대장주 전략은 **안정성과 단순성**이 장점이지만, **분산 효과가 제한적**입니다.

### 최종 권장 사항

1. **업종당 2개씩 → 총 10개 종목** 확대
2. **손절 규칙 엄격 준수** (-7% 또는 -10%)
3. **분기별 업종 로테이션** 점검
4. **AI 추천과 50:50 혼합** 고려 (총 15-20개)
5. **최소 6개월 이상** 장기 투자 관점 유지

### 투자 성향별 추천

| 성향 | 추천 전략 | 현금 비중 | 손절 기준 |
|------|----------|----------|----------|
| 보수적 | 업종별 대장주 | 30% | -7% |
| 중도적 | 하이브리드 | 20% | -10% |
| 공격적 | AI 전략 | 10% | -15% |

---

**작성일**: 2025-10-25
**버전**: 1.0

**면책 조항**: 본 가이드는 교육 및 연구 목적의 참고 자료이며, 투자 권유가 아닙니다. 모든 투자 판단과 그에 따른 손실은 투자자 본인의 책임입니다.
