# Phase 2: 종목별 주도주 리더십 점수 통합 - 완료

## 작업 개요
사용자의 요청에 따라 기존의 섹터 기반 대장주 시스템에서 종목별 주도주를 우선 선정하는 시스템으로 변경하였습니다.

## 완료된 작업

### 1. FactorScorer에 리더십 점수 통합
**파일: `core/modules/factor_scoring.py`**

#### 추가된 메서드:
- `calculate_leadership_score(df)`: 리더십 점수 계산
  - SectorLeaderDetector를 이용해 종목의 주도력 측정
  - 시가총액, 거래대금, 모멘텀, 재무 건전성, 안정성 종합 평가
  - 0-100 범위로 정규화

#### 수정된 메서드:
- `calculate_composite_score(df)`: 리더십 점수를 가중 계산에 포함
  - 가중치: leadership * 0.15

#### 가중치 설정:
- value: 20% (PER, PBR 기반 밸류에이션)
- growth: 20% (매출/이익 성장률)
- profitability: 20% (ROE, 영업이익률)
- momentum: 15% (기술적 모멘텀)
- stability: 10% (부채비율, 변동성)
- leadership: 15% (주도주 점수) ← 새로 추가

#### screen_stocks 함수 수정:
- Step 6에서 calculate_leadership_score() 호출 추가
- 파이프라인: value → growth → profitability → stability → leadership → momentum → composite

### 2. 주도주 전략 모듈 생성
**파일: `paper_trading/leader_strategy.py` (신규, 178 줄)**

#### 주요 함수:
1. `get_leader_recommendations()`:
   - 팩터 스크리닝으로 상위 N개 주도주 추천
   - 리더십 점수가 0보다 큰 종목 우선
   - 동일 가중치로 비중 배분

2. `get_leader_recommendations_by_sector()`:
   - 각 섹터에서 상위 N개 주도주 선정
   - 섹터별로 독립적인 순위 매기기
   - 총 가중치 1.0으로 정규화

#### 특징:
- FactorScorer를 래핑한 고수준 인터페이스
- 데이터베이스 직접 쿼리 대신 팩터 스크리닝 활용
- 안정적인 에러 핸들링 및 로깅

### 3. 주도주 전략을 trading_crew에 통합
**파일: `paper_trading/trading_crew.py`**

#### 변경사항:
1. argparse에 "leader" 전략 옵션 추가
   - choices: ["ai", "sector", "hybrid", "ai-sector", "leader"]

2. run_daily_trading_workflow에 leader 전략 처리 추가
   - Step 3에서 leader 전략 선택 시 leader_strategy.get_leader_recommendations() 호출
   - 다른 전략과 동일한 워크플로우 처리

3. 함수 docstring 업데이트
   - leader 전략 설명 추가
   - 사용 가능한 모든 전략 문서화

#### 사용 방법:
```bash
# 주도주 전략으로 일일 자동 매매 실행
python paper_trading/trading_crew.py --strategy leader --top-n 10 --execute

# 분석만 실행
python paper_trading/trading_crew.py --strategy leader --top-n 10
```

### 4. 테스트 및 검증
**파일: `tests/test_leadership_integration.py` (신규)**

#### 테스트 1: 리더십 점수 계산
- FactorScorer의 각 메서드 순차 호출 검증
- leadership_score 컬럼 추가 확인
- 종합 점수에 리더십 포함 여부 검증
- ✅ 테스트 통과

#### 테스트 2: 순위 매기기
- 리더십 점수를 포함한 순위 매기기 검증
- 상위 5개 종목 조회 및 출력
- ✅ 테스트 통과

#### 테스트 결과:
```
✅ 종합 점수 계산이 정확합니다
   예상값: 20.77, 실제값: 20.77
✅ 순위 매기기 완료 (상위 5개)
```

### 5. 버그 수정
**파일: `core/modules/sector_leader_detector.py`**

- 사용하지 않는 import 제거: `calculate_technical_indicators`
- 이를 통해 임포트 에러 해결

## 시스템 아키텍처

```
팩터 스크리닝 파이프라인
│
├─ FactorScorer 클래스
│  ├─ calculate_value_score()
│  ├─ calculate_growth_score()
│  ├─ calculate_profitability_score()
│  ├─ calculate_stability_score()
│  ├─ calculate_leadership_score() ← NEW
│  ├─ calculate_momentum_score()
│  └─ calculate_composite_score() ← UPDATED (includes leadership)
│
├─ SectorLeaderDetector 클래스
│  └─ 리더십 점수 계산에 사용됨
│
├─ leader_strategy 모듈 ← NEW
│  ├─ get_leader_recommendations()
│  └─ get_leader_recommendations_by_sector()
│
└─ trading_crew 워크플로우
   └─ --strategy leader 옵션 추가
```

## 주도주 판정 기준

리더십 점수는 다음 요소들을 종합적으로 평가합니다:

1. **시가총액 (35%)**
   - 로그 스케일로 1조-100조 범위 정규화
   - 시장 영향력 반영

2. **거래대금 (25%)**
   - 거래량 안정성(CV 기준) 반영
   - 유동성 평가

3. **모멘텀 (20%)**
   - 5일 vs 30일 이동평균 비교
   - 단기 상승세 평가

4. **재무 건전성 (15%)**
   - ROE, 부채비율, 영업이익률
   - 기업 기초체력 평가

5. **안정성 (5%)**
   - 변동성 및 최대낙폭
   - 위험도 평가

## 팩터 가중치 최적화

기존 5개 팩터 (100%):
- value: 25%, growth: 25%, profitability: 25%, momentum: 15%, stability: 10%

새로운 6개 팩터 (100%):
- value: 20%, growth: 20%, profitability: 20%, momentum: 15%, stability: 10%, leadership: 15%

→ 리더십을 15% 가중치로 포함하면서 다른 팩터들을 균형있게 조정

## 다음 단계 (향후 작업)

1. **통합 테스트**
   - 실제 시장 데이터로 leader 전략 검증
   - 다른 전략(ai, sector 등)과의 성과 비교

2. **성과 모니터링**
   - 주도주 선정 정확도 추적
   - 초과수익률(alpha) 분석

3. **파라미터 최적화**
   - 각 팩터의 가중치 튜닝
   - 리더십 점수 판정 기준 조정

4. **하이브리드 전략 확장**
   - leader + ai 혼합 (50:50)
   - leader + sector 혼합

## 코드 품질

- ✅ 에러 핸들링 완비
- ✅ 로깅 시스템 구축
- ✅ 문서화 완성 (docstring, 주석)
- ✅ 타입 힌팅 추가
- ✅ 테스트 작성 및 검증 완료

## 배포 준비

모든 파일이 프로덕션 준비 상태입니다:
- `core/modules/factor_scoring.py`: 핵심 로직
- `paper_trading/leader_strategy.py`: 전략 구현
- `paper_trading/trading_crew.py`: 통합 워크플로우
- `tests/test_leadership_integration.py`: 테스트 스위트
