# 주도주 전략 (Leader Strategy) - 빠른 시작 가이드

## 🚀 1초 요약

**팩터 스크리닝 기반의 동적 주도주 선정 시스템이 추가되었습니다.**
- 시가총액, 거래대금, 모멘텀, 재무, 안정성을 종합 평가
- 6개 팩터의 균형잡힌 점수 계산 (leadership 15% 포함)
- `--strategy leader` 옵션으로 사용 가능

---

## 📝 기본 사용법

### 터미널에서 바로 실행

```bash
# 분석만 실행 (매매 X)
cd /Users/yeongchang.jeon/workspace/ai-agent
python paper_trading/trading_crew.py --strategy leader --top-n 10

# 분석 + 실제 거래 실행 (10개 종목 매수)
python paper_trading/trading_crew.py --strategy leader --top-n 10 --execute

# KOSDAQ에서 상위 15개 주도주 선정
python paper_trading/trading_crew.py --strategy leader --market KOSDAQ --top-n 15

# 로그 저장하면서 실행
python paper_trading/trading_crew.py --strategy leader --execute --save-log
```

### Python 코드에서 사용

```python
from paper_trading.leader_strategy import get_leader_recommendations

# 주도주 추천 받기
recommendations = get_leader_recommendations(
    market="KOSPI",
    top_n=10
)

# 결과 확인
for rec in recommendations:
    print(f"Code: {rec['code']}")
    print(f"Reason: {rec['reason']}")
    print(f"Weight: {rec['weight']*100:.1f}%")
    print(f"Composite Score: {rec['composite_score']:.2f}")
    print(f"Leadership Score: {rec['leadership_score']:.2f}")
    print()
```

---

## 📊 팩터 설명

| 팩터 | 가중치 | 설명 | 범위 |
|------|--------|------|------|
| Value | 20% | 저평가 종목 선호 (PER, PBR) | 0-100 |
| Growth | 20% | 성장성 (매출/이익 성장률) | 0-100 |
| Profitability | 20% | 수익성 (ROE, 영업이익률) | 0-100 |
| Momentum | 15% | 단기 상승세 (가격 변화율) | 0-100 |
| Stability | 10% | 재무 안정성 (부채비율, 변동성) | 0-100 |
| **Leadership** | **15%** | **주도주 점수** (시가총액, 거래대금 등) | **0-100** |

---

## 🎯 주도주 점수 계산

리더십 점수 = 35% × 시가총액 + 25% × 거래대금 + 20% × 모멘텀 + 15% × 재무건전성 + 5% × 안정성

**예시**: 삼성전자(005930)
- 시가총액: 높음 (100조 이상) → 35점
- 거래대금: 높은 유동성 → 25점
- 모멘텀: 상승세 → 20점
- 재무: 우수 (ROE 15%, 부채비 45%) → 15점
- 안정성: 낮은 변동성 → 5점
- **총 리더십 점수: 95점** ⭐

---

## 💡 다른 전략과 비교

| 전략 | 선정 기준 | 장점 | 단점 |
|------|---------|------|------|
| **ai** | AI 에이전트 분석 | 깊이 있음 | 시간 오래 걸림 (수 분) |
| **sector** | 업종별 고정 대장주 | 빠름 | 동적 변화 반영 X |
| **leader** ⭐ | 팩터 기반 주도주 | 정량적/동적 | 데이터 필요 |
| **hybrid** | AI 50% + 대장주 50% | 균형 | 복잡함 |
| **ai-sector** | 거래량 중심 대장주 | 유동성 중심 | 재무 정보 미반영 |

---

## ⚙️ 옵션 설정

```bash
# 필수 옵션
--strategy leader           # 주도주 전략 사용

# 선택 옵션 (기본값)
--account-id 1              # 계좌 ID (기본: 1)
--market KOSPI              # 시장 (KOSPI/KOSDAQ, 기본: KOSPI)
--top-n 10                  # 선정 종목 수 (기본: 10)
--limit 20                  # 분석 종목 수 (기본: 20)
--cash-reserve 0.2          # 현금 보유 비율 (기본: 20%)
--stop-loss -10.0           # 손절 기준 (기본: -10%)
--take-profit 20.0          # 익절 기준 (기본: +20%)
--execute                   # 실제 거래 실행 (플래그)
--save-log                  # 결과 로그 저장 (플래그)
```

### 예시

```bash
# 상위 15개 주도주, 현금 10% 보유, 손절 -5%, 익절 25%
python paper_trading/trading_crew.py \
    --strategy leader \
    --top-n 15 \
    --cash-reserve 0.1 \
    --stop-loss -5.0 \
    --take-profit 25.0 \
    --execute \
    --save-log
```

---

## 🔧 가중치 커스터마이징

기본 가중치 대신 커스텀 가중치를 사용하려면:

```python
from paper_trading.leader_strategy import get_leader_recommendations

custom_weights = {
    'value': 0.25,          # 밸류 중시 (기본 20%)
    'growth': 0.15,         # 성장성 축소 (기본 20%)
    'profitability': 0.20,
    'momentum': 0.15,
    'stability': 0.10,
    'leadership': 0.15      # 리더십은 15% 고정 권장
}

recommendations = get_leader_recommendations(
    top_n=10,
    weights=custom_weights
)
```

**중요**: 가중치의 합은 반드시 1.0이어야 합니다!

---

## 📈 실행 결과 해석

```
📅 일일 자동 매매 워크플로 - 2025-10-30 21:41:00
================================================================================

[Step 1] 포트폴리오 업데이트
✅ 10개 종목 업데이트 완료
   총 평가액: 10,000,000원

[Step 2] 손절/익절 체크
✅ 손절/익절 대상 없음

[Step 3] 투자 분석 (전략: LEADER)
주도주 전략 실행 (팩터 기반 리더십 점수)

팩터 스크리닝 실행 (상위 10개)...
✅ 10개 주도주 선정 완료

선정된 주도주:
   • 005930: 종합점수 87.5, 리더십 92.3  ← 시가총액 큼, 거래량 많음
   • 000660: 종합점수 84.2, 리더십 88.1
   • 035420: 종합점수 79.8, 리더십 85.5
   ...

📊 추천 종목 (10개):
   • 005930: 10.0%
   • 000660: 10.0%
   ...

[Step 4] 매수 실행
초기 포트폴리오 구성
============================================================
총 10개 종목 매수 예정

📊 005930: 3주 @ 70,000원 = 210,000원
   ✅ 매수 체결: 210,000원
...

============================================================
매수 완료: 10/10건
총 투자 금액: 8,000,000원
============================================================

[Step 5] 일일 스냅샷 저장
✅ 스냅샷 저장 완료
   총 자산: 10,000,000원
   수익률: 0.00%

================================================================================
✅ 일일 워크플로 완료
================================================================================
```

---

## 🐛 문제 해결

### Q: "리더십 점수가 0으로 나옵니다"

**A**: 데이터베이스에 필요한 정보가 없을 수 있습니다.
- 확인: stocks, prices, financials 테이블의 데이터 존재 여부
- 해결: 데이터 수집 완료 후 재실행

### Q: "스크리닝이 매우 느립니다"

**A**: 팩터 스크리닝은 모든 종목을 평가하므로 수십 초 소요됩니다.
- 첫 실행은 더 느릴 수 있음
- 데이터베이스 인덱스 확인

### Q: "가중치 합 오류"

**A**: 커스텀 가중치의 합이 1.0이어야 합니다.
```python
# ❌ 잘못됨
weights = {'value': 0.3, 'growth': 0.3, ...}  # 합 > 1.0

# ✅ 올바름
weights = {'value': 0.25, 'growth': 0.25, ...}  # 합 = 1.0
```

### Q: "--execute 없이 분석만 하고 싶어요"

**A**: `--execute` 플래그를 빼면 됩니다.
```bash
# 분석만 실행 (실제 매수 안 함)
python paper_trading/trading_crew.py --strategy leader --top-n 10
```

---

## 📚 추가 문서

- [상세 가이드](PHASE2_LEADER_STRATEGY.md): 아키텍처, 성과 지표, 유지보수
- [팩터 스크리닝 가이드](../core/modules/factor_scoring.py): 코드 레벨 상세
- [테스트 코드](../tests/test_leadership_integration.py): 구현 예시

---

## ✨ 핵심 특징

1. **동적 리더십 점수**
   - 시장 변화에 실시간 반영
   - 매 분석마다 주도주가 업데이트됨

2. **6개 팩터 종합 평가**
   - 단일 지표 의존 X
   - 밸런스 잡힌 종목 선정

3. **정량적 기준**
   - 주관적 판단 최소화
   - 재현 가능한 결과

4. **기존 시스템 통합**
   - ai, sector, hybrid 전략과 함께 사용 가능
   - 손절/익절, 제외 종목 기능 모두 지원

---

## 🎓 다음 학습

1. **성과 모니터링**: leader 전략의 초과수익률 추적
2. **가중치 최적화**: 자신의 투자 스타일에 맞게 조정
3. **혼합 전략**: leader + ai 또는 leader + sector 결합

---

**최종 업데이트**: 2025-10-30
**상태**: ✅ 프로덕션 준비 완료
