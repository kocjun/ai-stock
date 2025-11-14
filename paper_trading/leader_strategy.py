"""
주도주 전략 (Leader Strategy)

팩터 스크리닝을 통해 각 종목의 리더십 점수를 포함한 종합 점수를 계산하고
상위 종목을 추천합니다.

FactorScorer를 사용하여 다양한 팩터를 고려한 동적 주도주 선정:
- value: 밸류에이션 지표 (PER, PBR)
- growth: 성장성 지표 (매출/이익 성장률)
- profitability: 수익성 지표 (ROE, 영업이익률)
- momentum: 기술적 모멘텀 (가격 상승률)
- stability: 안정성 지표 (부채비율, 변동성)
- leadership: 주도주 점수 (시가총액, 거래대금, 모멘텀, 재무, 안정성)
"""

import sys
import logging
from pathlib import Path
from typing import List, Dict, Optional
import pandas as pd
import numpy as np

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from core.modules.factor_scoring import screen_stocks
from core.utils.db_utils import get_db_connection

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_leader_recommendations(
    market: str = "KOSPI",
    top_n: int = 10,
    weights: Optional[Dict[str, float]] = None,
    min_roe: float = 0,
    max_debt_ratio: float = 200
) -> List[Dict]:
    """
    주도주 전략을 통한 종목 추천

    팩터 스크리닝을 통해 리더십 점수를 포함한 종합 점수가 높은 종목을 추천합니다.

    Args:
        market: 시장 (KOSPI 또는 KOSDAQ) - 현재는 미사용 (화면_stocks이 자동으로 처리)
        top_n: 추천 종목 수
        weights: 팩터별 가중치 커스터마이징
                (기본값: value/growth/profitability/momentum 각 20%,
                         stability 10%, leadership 15%)
        min_roe: 최소 ROE (%)
        max_debt_ratio: 최대 부채비율 (%)

    Returns:
        List[Dict]: 추천 종목 리스트
            - code: 종목 코드
            - weight: 추천 비중 (0-1)
            - reason: 선정 사유
            - rank: 순위
            - composite_score: 종합 점수
            - leadership_score: 주도주 점수
    """
    logger.info("="*60)
    logger.info("주도주 전략 실행 시작")
    logger.info("="*60)

    try:
        # 팩터 스크리닝 실행
        logger.info(f"\n팩터 스크리닝 실행 (상위 {top_n}개)...")
        screened_stocks = screen_stocks(
            top_n=top_n,
            weights=weights,
            min_roe=min_roe,
            max_debt_ratio=max_debt_ratio
        )

        if screened_stocks.empty:
            logger.warning("스크리닝 결과가 없습니다")
            return []

        # 주도주 점수가 0이 아닌 종목만 필터링 (리더십 점수가 있는 종목)
        leader_stocks = screened_stocks[screened_stocks.get('leadership_score', 0) > 0].copy()

        if leader_stocks.empty:
            logger.warning("리더십 점수가 있는 주도주가 없습니다. 전체 스크리닝 결과를 사용합니다")
            leader_stocks = screened_stocks.copy()

        # 종목 코드 및 주도주 점수로 정렬
        leader_stocks = leader_stocks.sort_values('composite_score', ascending=False)

        # 추천 종목 구성
        recommendations = []
        equal_weight = 1.0 / len(leader_stocks) if len(leader_stocks) > 0 else 0

        for idx, row in leader_stocks.iterrows():
            code = row.get('code')
            rank = row.get('rank', idx + 1)
            composite_score = row.get('composite_score', 0)
            leadership_score = row.get('leadership_score', 0)

            recommendation = {
                'code': code,
                'weight': equal_weight,
                'reason': f"주도주 전략 (순위: {rank}, 점수: {composite_score:.1f}, 리더십: {leadership_score:.1f})",
                'rank': rank,
                'composite_score': float(composite_score),
                'leadership_score': float(leadership_score)
            }

            recommendations.append(recommendation)

        logger.info(f"\n✅ {len(recommendations)}개 주도주 선정 완료")
        logger.info("\n선정된 주도주:")
        for rec in recommendations:
            logger.info(f"   • {rec['code']}: 종합점수 {rec['composite_score']:.1f}, "
                       f"리더십 {rec['leadership_score']:.1f}")

        logger.info("="*60)

        return recommendations

    except Exception as e:
        logger.error(f"주도주 전략 실행 실패: {e}", exc_info=True)
        return []


def get_leader_recommendations_by_sector(
    market: str = "KOSPI",
    leaders_per_sector: int = 2,
    weights: Optional[Dict[str, float]] = None,
    min_roe: float = 0,
    max_debt_ratio: float = 200
) -> List[Dict]:
    """
    섹터별 주도주 추천

    각 섹터에서 리더십 점수 기반 상위 N개 주도주를 추천합니다.

    Args:
        market: 시장 (KOSPI 또는 KOSDAQ)
        leaders_per_sector: 섹터당 추천 주도주 수
        weights: 팩터별 가중치 커스터마이징
        min_roe: 최소 ROE (%)
        max_debt_ratio: 최대 부채비율 (%)

    Returns:
        List[Dict]: 추천 종목 리스트 (섹터별로 최대 leaders_per_sector개)
    """
    logger.info("="*60)
    logger.info(f"섹터별 주도주 전략 실행 (섹터당 {leaders_per_sector}개)")
    logger.info("="*60)

    try:
        # 팩터 스크리닝 실행 (충분한 수의 종목)
        all_screened = screen_stocks(
            top_n=100,  # 충분한 수의 종목을 먼저 스크리닝
            weights=weights,
            min_roe=min_roe,
            max_debt_ratio=max_debt_ratio
        )

        if all_screened.empty:
            logger.warning("스크리닝 결과가 없습니다")
            return []

        recommendations = []

        # 섹터별로 상위 N개 선택
        if 'sector' in all_screened.columns:
            for sector in all_screened['sector'].unique():
                if pd.isna(sector):
                    continue

                sector_stocks = all_screened[all_screened['sector'] == sector].copy()
                sector_stocks = sector_stocks.sort_values('composite_score', ascending=False)

                # 섹터당 상위 leaders_per_sector개
                top_leaders = sector_stocks.head(leaders_per_sector)

                equal_weight = 1.0 / (len(all_screened) / leaders_per_sector)

                logger.info(f"\n{sector} 섹터:")
                for rank, (idx, row) in enumerate(top_leaders.iterrows(), 1):
                    code = row.get('code')
                    composite_score = row.get('composite_score', 0)
                    leadership_score = row.get('leadership_score', 0)

                    recommendation = {
                        'code': code,
                        'weight': equal_weight,
                        'reason': f"{sector} 주도주 (순위: {rank}, 점수: {composite_score:.1f})",
                        'sector': sector,
                        'rank': rank,
                        'composite_score': float(composite_score),
                        'leadership_score': float(leadership_score)
                    }

                    recommendations.append(recommendation)
                    logger.info(f"   • {code}: 종합점수 {composite_score:.1f}, "
                               f"리더십 {leadership_score:.1f}")

        else:
            logger.warning("섹터 정보가 없습니다. 전체 주도주로 추천합니다")
            return get_leader_recommendations(
                market=market,
                top_n=leaders_per_sector * 5,  # 대략 5개 섹터 기준
                weights=weights,
                min_roe=min_roe,
                max_debt_ratio=max_debt_ratio
            )

        # 가중치 정규화
        if recommendations:
            total_weight = sum(r['weight'] for r in recommendations)
            for rec in recommendations:
                rec['weight'] = rec['weight'] / total_weight if total_weight > 0 else 1.0 / len(recommendations)

        logger.info(f"\n✅ {len(recommendations)}개 주도주 선정 완료")
        logger.info("="*60)

        return recommendations

    except Exception as e:
        logger.error(f"섹터별 주도주 전략 실행 실패: {e}", exc_info=True)
        return []


if __name__ == "__main__":
    """테스트 실행"""
    print("\n" + "="*60)
    print("주도주 전략 테스트")
    print("="*60)

    # 테스트 1: 전체 주도주 추천
    print("\n[테스트 1] 전체 주도주 추천")
    recommendations = get_leader_recommendations(top_n=10)
    print(f"\n추천 종목: {len(recommendations)}개")
    for rec in recommendations:
        print(f"  • {rec['code']}: {rec['reason']}")

    # 테스트 2: 섹터별 주도주 추천
    print("\n[테스트 2] 섹터별 주도주 추천")
    sector_recommendations = get_leader_recommendations_by_sector(leaders_per_sector=2)
    print(f"\n추천 종목: {len(sector_recommendations)}개")
    for rec in sector_recommendations:
        print(f"  • {rec['code']} ({rec.get('sector', 'N/A')}): {rec['reason']}")

    print("\n" + "="*60)
