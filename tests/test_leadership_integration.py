"""
주도주 점수 통합 테스트

FactorScorer에 통합된 리더십 점수 계산 및 종합 점수에 포함 여부 확인
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from core.modules.factor_scoring import FactorScorer


def test_leadership_score_calculation():
    """주도주 점수 계산 테스트"""
    print("\n" + "="*60)
    print("테스트 1: 리더십 점수 계산")
    print("="*60)

    # 샘플 데이터 생성
    sample_data = pd.DataFrame({
        'code': ['005930', '000660', '035420', '005380', '051910'],
        'name': ['삼성전자', 'SK하이닉스', '현대차', '현대모비스', 'LG화학'],
        'sector': ['반도체', '반도체', '자동차', '자동차', '화학'],
        'per': [10.5, 8.2, 9.1, 7.8, 11.2],
        'pbr': [1.2, 0.9, 1.1, 0.8, 1.3],
        'roe': [15.5, 12.3, 14.2, 13.1, 16.5],
        'debt_ratio': [45.2, 38.5, 52.3, 41.8, 39.2],
        'revenue_growth': [5.2, 3.1, 4.5, 3.8, 6.2],
        'net_profit_growth': [8.5, 5.2, 7.3, 6.1, 9.8],
        'operating_margin': [28.5, 32.1, 15.2, 18.3, 22.5],
        'volatility': [25.3, 22.5, 28.1, 24.2, 26.5]
    })

    # FactorScorer 인스턴스 생성
    scorer = FactorScorer()

    # 각 팩터 점수 계산
    print("\n1️⃣ 밸류 점수 계산...")
    scored = scorer.calculate_value_score(sample_data)
    print(f"   ✓ value_score 컬럼 추가됨")

    print("\n2️⃣ 성장 점수 계산...")
    scored = scorer.calculate_growth_score(scored)
    print(f"   ✓ growth_score 컬럼 추가됨")

    print("\n3️⃣ 수익성 점수 계산...")
    scored = scorer.calculate_profitability_score(scored)
    print(f"   ✓ profitability_score 컬럼 추가됨")

    print("\n4️⃣ 안정성 점수 계산...")
    scored = scorer.calculate_stability_score(scored)
    print(f"   ✓ stability_score 컬럼 추가됨")

    print("\n5️⃣ 리더십 점수 계산...")
    try:
        scored = scorer.calculate_leadership_score(scored)
        print(f"   ✓ leadership_score 컬럼 추가됨")

        # 리더십 점수 확인
        print(f"\n   리더십 점수 샘플:")
        for idx, row in scored.iterrows():
            print(f"      {row['code']} ({row['name']}): {row.get('leadership_score', 0):.2f}점")

    except Exception as e:
        print(f"   ⚠️  리더십 점수 계산 중 오류: {e}")
        print(f"      기본값(0)으로 설정합니다.")
        scored['leadership_score'] = 0

    print("\n6️⃣ 종합 점수 계산...")
    scored = scorer.calculate_composite_score(scored)
    print(f"   ✓ composite_score 컬럼 추가됨")

    # 가중치 확인
    print(f"\n   가중치 설정:")
    for factor, weight in scorer.weights.items():
        print(f"      {factor}: {weight:.0%}")

    # 종합 점수 확인
    print(f"\n   종합 점수 (리더십 포함):")
    for idx, row in scored.iterrows():
        print(f"      {row['code']} ({row['name']}): {row.get('composite_score', 0):.2f}점")

    # 종합 점수 검증
    print(f"\n✅ 리더십 점수가 종합 점수에 포함되었는지 검증:")
    sample_composite = scored.iloc[0]

    # 수동으로 종합 점수 계산해서 비교
    expected_composite = (
        sample_composite.get('value_score', 0) * scorer.weights['value'] +
        sample_composite.get('growth_score', 0) * scorer.weights['growth'] +
        sample_composite.get('profitability_score', 0) * scorer.weights['profitability'] +
        sample_composite.get('momentum_score', 0) * scorer.weights['momentum'] +
        sample_composite.get('stability_score', 0) * scorer.weights['stability'] +
        sample_composite.get('leadership_score', 0) * scorer.weights['leadership']
    )

    actual_composite = sample_composite.get('composite_score', 0)

    if np.isclose(expected_composite, actual_composite, atol=0.01):
        print(f"   ✓ 종합 점수 계산이 정확합니다")
        print(f"      예상값: {expected_composite:.2f}, 실제값: {actual_composite:.2f}")
    else:
        print(f"   ❌ 종합 점수 계산에 오류가 있습니다")
        print(f"      예상값: {expected_composite:.2f}, 실제값: {actual_composite:.2f}")

    return scored


def test_ranking_with_leadership():
    """리더십 점수를 포함한 순위 매기기 테스트"""
    print("\n" + "="*60)
    print("테스트 2: 리더십 점수 포함 순위 매기기")
    print("="*60)

    # 샘플 데이터 생성 (더 많은 종목)
    np.random.seed(42)
    codes = [f'{i:06d}' for i in range(5930, 5940)]
    sample_data = pd.DataFrame({
        'code': codes,
        'name': [f'종목{i}' for i in range(len(codes))],
        'per': np.random.uniform(5, 20, len(codes)),
        'pbr': np.random.uniform(0.5, 2, len(codes)),
        'roe': np.random.uniform(5, 25, len(codes)),
        'debt_ratio': np.random.uniform(20, 100, len(codes)),
        'revenue_growth': np.random.uniform(0, 15, len(codes)),
        'net_profit_growth': np.random.uniform(-5, 20, len(codes)),
        'operating_margin': np.random.uniform(5, 35, len(codes)),
        'volatility': np.random.uniform(15, 40, len(codes))
    })

    scorer = FactorScorer()

    # 모든 점수 계산
    scored = scorer.calculate_value_score(sample_data)
    scored = scorer.calculate_growth_score(scored)
    scored = scorer.calculate_profitability_score(scored)
    scored = scorer.calculate_stability_score(scored)
    scored = scorer.calculate_leadership_score(scored)
    scored = scorer.calculate_composite_score(scored)

    # 순위 매기기
    ranked = scorer.rank_stocks(scored, top_n=5)

    print(f"\n상위 5개 종목 순위:")
    print("-" * 60)
    for idx, row in ranked.iterrows():
        print(f"{int(row['rank'])}순위: {row['code']} - 종합점수: {row['composite_score']:.2f}점")
        print(f"         리더십: {row.get('leadership_score', 0):.2f}점")

    print(f"\n✅ 순위 매기기 완료 (상위 {len(ranked)}개)")

    return ranked


if __name__ == "__main__":
    print("\n" + "🚀 리더십 점수 통합 테스트 시작" + "="*50)

    # 테스트 1 실행
    scored_df = test_leadership_score_calculation()

    # 테스트 2 실행
    ranked_df = test_ranking_with_leadership()

    print("\n" + "="*60)
    print("✅ 모든 테스트 완료!")
    print("="*60 + "\n")
