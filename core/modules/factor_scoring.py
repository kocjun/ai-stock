"""
팩터 스코어링 시스템

다양한 투자 팩터를 조합하여 종목별 종합 점수를 계산합니다.

주요 팩터:
- 밸류 (Value): PER, PBR
- 성장 (Growth): 매출/이익 성장률
- 수익성 (Profitability): ROE, 영업이익률
- 모멘텀 (Momentum): 가격 변화율
- 안정성 (Stability): 부채비율, 변동성
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from core.modules.financial_metrics import (
    get_financial_data_from_db,
    get_latest_prices_from_db,
    calculate_basic_ratios,
    calculate_profitability_metrics,
    calculate_growth_rates
)
from core.utils.db_utils import get_db_connection


class FactorScorer:
    """팩터 기반 종목 스코어링 시스템"""

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        """
        Args:
            weights: 팩터별 가중치 (합이 1.0이 되어야 함)
                     기본값: {'value': 0.20, 'growth': 0.20, 'profitability': 0.20, 'momentum': 0.15, 'stability': 0.10, 'leadership': 0.15}
        """
        if weights is None:
            self.weights = {
                'value': 0.20,
                'growth': 0.20,
                'profitability': 0.20,
                'momentum': 0.15,
                'stability': 0.10,
                'leadership': 0.15  # 새로 추가: 주도주 점수
            }
        else:
            # 가중치 합이 1.0인지 확인
            total = sum(weights.values())
            if not np.isclose(total, 1.0):
                raise ValueError(f"가중치 합이 1.0이 아닙니다: {total}")
            self.weights = weights

    def calculate_value_score(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        밸류 팩터 점수 계산 (0-100점)

        낮은 PER, PBR일수록 높은 점수
        """
        result = df.copy()

        # PER 점수 (0-50점)
        if 'per' in result.columns:
            # PER 역수를 정규화 (0-1)
            per_inverse = 1 / result['per'].replace([np.inf, -np.inf], np.nan)
            per_normalized = (per_inverse - per_inverse.min()) / (per_inverse.max() - per_inverse.min())
            result['per_score'] = per_normalized * 50
            result['per_score'] = result['per_score'].fillna(0)

        # PBR 점수 (0-50점)
        if 'pbr' in result.columns:
            # PBR 역수를 정규화 (0-1)
            pbr_inverse = 1 / result['pbr'].replace([np.inf, -np.inf], np.nan)
            pbr_normalized = (pbr_inverse - pbr_inverse.min()) / (pbr_inverse.max() - pbr_inverse.min())
            result['pbr_score'] = pbr_normalized * 50
            result['pbr_score'] = result['pbr_score'].fillna(0)

        # 밸류 종합 점수
        result['value_score'] = (result.get('per_score', 0) + result.get('pbr_score', 0))

        return result

    def calculate_growth_score(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        성장 팩터 점수 계산 (0-100점)

        높은 매출/이익 성장률일수록 높은 점수
        """
        result = df.copy()

        # 매출 성장률 점수 (0-50점)
        if 'revenue_growth' in result.columns:
            # 음수 성장률은 0점
            revenue_growth_pos = result['revenue_growth'].clip(lower=0)
            # 0-50% 성장을 0-50점으로 매핑
            result['revenue_growth_score'] = revenue_growth_pos.clip(upper=50)

        # 순이익 성장률 점수 (0-50점)
        if 'net_profit_growth' in result.columns:
            profit_growth_pos = result['net_profit_growth'].clip(lower=0)
            result['profit_growth_score'] = profit_growth_pos.clip(upper=50)

        # 성장 종합 점수
        result['growth_score'] = (
            result.get('revenue_growth_score', 0) +
            result.get('profit_growth_score', 0)
        )

        return result

    def calculate_profitability_score(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        수익성 팩터 점수 계산 (0-100점)

        높은 ROE, 영업이익률일수록 높은 점수
        """
        result = df.copy()

        # ROE 점수 (0-50점)
        if 'roe' in result.columns:
            # ROE 0-50%를 0-50점으로 매핑
            result['roe_score'] = result['roe'].clip(lower=0, upper=50)

        # 영업이익률 점수 (0-50점)
        if 'operating_margin' in result.columns:
            # 영업이익률 0-50%를 0-50점으로 매핑
            result['operating_margin_score'] = result['operating_margin'].clip(lower=0, upper=50)

        # 수익성 종합 점수
        result['profitability_score'] = (
            result.get('roe_score', 0) +
            result.get('operating_margin_score', 0)
        )

        return result

    def calculate_momentum_score(self, df: pd.DataFrame, periods: List[int] = [20, 60, 120]) -> pd.DataFrame:
        """
        모멘텀 팩터 점수 계산 (0-100점)

        최근 가격 상승률이 높을수록 높은 점수

        Args:
            df: 가격 데이터 DataFrame (code, date, close 컬럼 필요)
            periods: 계산할 기간 리스트 (일수)
        """
        result = df.copy()

        scores = []
        for period in periods:
            col_name = f'return_{period}d'
            # 기간별 수익률 계산
            result[col_name] = result.groupby('code')['close'].pct_change(period) * 100

            # 수익률을 점수로 변환 (0-33점)
            score_col = f'momentum_{period}d_score'
            result[score_col] = result[col_name].clip(lower=-50, upper=50)  # -50% ~ +50%
            result[score_col] = (result[score_col] + 50) / 3  # 0-33점으로 정규화
            scores.append(score_col)

        # 모멘텀 종합 점수 (평균)
        result['momentum_score'] = result[scores].mean(axis=1).fillna(0)

        return result

    def calculate_stability_score(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        안정성 팩터 점수 계산 (0-100점)

        낮은 부채비율, 낮은 변동성일수록 높은 점수
        """
        result = df.copy()

        # 부채비율 점수 (0-50점)
        if 'debt_ratio' in result.columns:
            # 부채비율이 낮을수록 높은 점수
            # 0%=50점, 100%=25점, 200%+=0점
            result['debt_score'] = 50 - (result['debt_ratio'].clip(upper=200) / 4)
            result['debt_score'] = result['debt_score'].clip(lower=0)

        # 가격 변동성 점수 (0-50점)
        if 'volatility' in result.columns:
            # 변동성이 낮을수록 높은 점수
            vol_normalized = (result['volatility'] - result['volatility'].min()) / (
                result['volatility'].max() - result['volatility'].min()
            )
            result['volatility_score'] = (1 - vol_normalized) * 50
            result['volatility_score'] = result['volatility_score'].fillna(25)  # 기본값 25점
        else:
            result['volatility_score'] = 25  # 변동성 데이터 없으면 중간값

        # 안정성 종합 점수
        result['stability_score'] = (
            result.get('debt_score', 0) +
            result.get('volatility_score', 0)
        )

        return result

    def calculate_leadership_score(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        주도주 점수 계산 (0-100점)

        종목의 섹터 내 주도력을 측정합니다.
        시가총액, 거래대금, 모멘텀, 재무 건전성, 안정성을 종합적으로 평가합니다.

        Returns:
            leadership_score 컬럼이 추가된 DataFrame
        """
        from core.modules.sector_leader_detector import SectorLeaderDetector

        result = df.copy()

        # 리더십 감지기 초기화
        detector = SectorLeaderDetector()

        try:
            # 모든 종목의 리더십 점수 계산
            leaders_by_sector = detector.detect_leaders()

            # 각 종목에 대한 리더십 점수 매핑
            leadership_scores = {}

            for sector, leader_list in leaders_by_sector.items():
                for leader_info in leader_list:
                    code = leader_info['code']
                    # 종합 리더십 점수 (0-100)
                    leadership_scores[code] = leader_info['overall_score']

            # DataFrame에 리더십 점수 추가
            result['leadership_score'] = result['code'].map(leadership_scores).fillna(0)

            # 0-100 범위로 정규화
            result['leadership_score'] = result['leadership_score'].clip(0, 100)

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"리더십 점수 계산 실패: {e}. 기본값 0으로 설정합니다.")
            result['leadership_score'] = 0

        return result

    def calculate_composite_score(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        종합 점수 계산 (0-100점)

        각 팩터 점수를 가중 평균
        """
        result = df.copy()

        result['composite_score'] = (
            result.get('value_score', 0) * self.weights['value'] +
            result.get('growth_score', 0) * self.weights['growth'] +
            result.get('profitability_score', 0) * self.weights['profitability'] +
            result.get('momentum_score', 0) * self.weights['momentum'] +
            result.get('stability_score', 0) * self.weights['stability'] +
            result.get('leadership_score', 0) * self.weights['leadership']
        )

        return result

    def rank_stocks(self, df: pd.DataFrame, top_n: int = 20) -> pd.DataFrame:
        """
        종목 순위 매기기

        Args:
            df: 점수가 계산된 DataFrame
            top_n: 상위 N개 종목

        Returns:
            상위 N개 종목 DataFrame
        """
        result = df.copy()

        # 종합 점수로 정렬
        result = result.sort_values('composite_score', ascending=False)

        # 순위 추가
        result['rank'] = range(1, len(result) + 1)

        # 상위 N개
        return result.head(top_n)


def calculate_price_volatility(stock_codes: List[str], days: int = 60) -> pd.DataFrame:
    """
    가격 변동성 계산

    Args:
        stock_codes: 종목 코드 리스트
        days: 계산 기간 (일수)

    Returns:
        변동성 DataFrame (code, volatility)
    """
    conn = get_db_connection()

    query = """
    SELECT code, date, close
    FROM prices
    WHERE code = ANY(%s)
        AND date >= CURRENT_DATE - INTERVAL '%s days'
    ORDER BY code, date
    """

    df = pd.read_sql_query(query, conn, params=(stock_codes, days))
    conn.close()

    # 일별 수익률 계산
    df['return'] = df.groupby('code')['close'].pct_change()

    # 변동성 (표준편차)
    volatility = df.groupby('code')['return'].std() * np.sqrt(252) * 100  # 연율화

    result = pd.DataFrame({
        'code': volatility.index,
        'volatility': volatility.values
    })

    return result


def screen_stocks(
    top_n: int = 20,
    weights: Optional[Dict[str, float]] = None,
    min_roe: float = 0,
    max_debt_ratio: float = 200
) -> pd.DataFrame:
    """
    종목 스크리닝 메인 함수

    Args:
        top_n: 상위 N개 종목
        weights: 팩터별 가중치
        min_roe: 최소 ROE (%)
        max_debt_ratio: 최대 부채비율 (%)

    Returns:
        스크리닝 결과 DataFrame
    """
    print("📊 종목 스크리닝 시작...")

    # 1. 재무 데이터 조회
    print("1. 재무 데이터 조회 중...")
    financial_df = get_financial_data_from_db()

    if financial_df.empty:
        print("❌ 재무 데이터가 없습니다.")
        return pd.DataFrame()

    # 최신 데이터만 (종목별 최신 분기)
    latest_financial = financial_df.groupby('code').tail(1).reset_index(drop=True)

    # 2. 재무 지표 계산
    print("2. 재무 지표 계산 중...")
    metrics = calculate_basic_ratios(latest_financial)
    metrics = calculate_profitability_metrics(metrics)

    # 3. 필터링
    print(f"3. 필터링 중 (ROE >= {min_roe}%, 부채비율 <= {max_debt_ratio}%)...")
    filtered = metrics[
        (metrics['roe'] >= min_roe) &
        (metrics['debt_ratio'] <= max_debt_ratio)
    ].copy()

    print(f"   필터링 후 종목 수: {len(filtered)}")

    if filtered.empty:
        print("❌ 필터링 후 종목이 없습니다.")
        return pd.DataFrame()

    # 4. 성장률 계산 (전체 데이터 필요)
    print("4. 성장률 계산 중...")
    growth_df = calculate_growth_rates(financial_df, periods=4)
    latest_growth = growth_df.groupby('code').tail(1).reset_index(drop=True)

    # filtered와 병합
    filtered = filtered.merge(
        latest_growth[['code', 'revenue_growth', 'operating_profit_growth', 'net_profit_growth']],
        on='code',
        how='left',
        suffixes=('', '_y')
    )

    # 5. 가격 데이터 및 변동성
    print("5. 가격 데이터 및 변동성 계산 중...")
    stock_codes = filtered['code'].tolist()

    # 최근 120일 가격 데이터 조회
    conn = get_db_connection()
    price_query = """
    SELECT code, date, close
    FROM prices
    WHERE code = ANY(%s)
        AND date >= CURRENT_DATE - INTERVAL '120 days'
    ORDER BY code, date
    """
    price_df = pd.read_sql_query(price_query, conn, params=(stock_codes,))
    conn.close()

    if not price_df.empty:
        # 변동성 계산
        volatility = calculate_price_volatility(stock_codes, days=60)
        filtered = filtered.merge(volatility, on='code', how='left')
    else:
        filtered['volatility'] = np.nan

    # 6. 팩터 점수 계산
    print("6. 팩터 점수 계산 중...")
    scorer = FactorScorer(weights)

    scored = scorer.calculate_value_score(filtered)
    scored = scorer.calculate_growth_score(scored)
    scored = scorer.calculate_profitability_score(scored)
    scored = scorer.calculate_stability_score(scored)
    scored = scorer.calculate_leadership_score(scored)  # 주도주 점수 추가

    # 모멘텀은 가격 데이터가 있을 때만
    if not price_df.empty:
        # 최신 가격만
        latest_prices = price_df.groupby('code').tail(1).reset_index(drop=True)
        scored = scored.merge(latest_prices[['code', 'close']], on='code', how='left')
        scored = scorer.calculate_momentum_score(price_df)
        scored = scored.groupby('code').tail(1).reset_index(drop=True)
    else:
        scored['momentum_score'] = 0

    # 7. 종합 점수 및 순위
    print("7. 종합 점수 계산 및 순위 매기기...")
    scored = scorer.calculate_composite_score(scored)
    result = scorer.rank_stocks(scored, top_n=top_n)

    print(f"✅ 스크리닝 완료! 상위 {len(result)}개 종목 선정")

    return result


def format_screening_result(df: pd.DataFrame) -> str:
    """
    스크리닝 결과를 보기 좋게 포맷

    Args:
        df: 스크리닝 결과 DataFrame

    Returns:
        포맷된 문자열
    """
    if df.empty:
        return "스크리닝 결과가 없습니다."

    output = ["=" * 80]
    output.append("종목 스크리닝 결과")
    output.append("=" * 80)
    output.append("")

    for idx, row in df.iterrows():
        output.append(f"[{row['rank']}위] {row['name']} ({row['code']}) - {row['sector']}")
        output.append(f"  종합 점수: {row['composite_score']:.1f}/100")
        output.append(f"  - 밸류: {row.get('value_score', 0):.1f}  성장: {row.get('growth_score', 0):.1f}  수익성: {row.get('profitability_score', 0):.1f}")
        output.append(f"  - 모멘텀: {row.get('momentum_score', 0):.1f}  안정성: {row.get('stability_score', 0):.1f}")
        output.append(f"  재무: ROE {row['roe']:.1f}%  부채비율 {row['debt_ratio']:.1f}%  영업이익률 {row.get('operating_margin', 0):.1f}%")
        output.append(f"  성장: 매출 {row.get('revenue_growth', 0):.1f}%  이익 {row.get('net_profit_growth', 0):.1f}%")
        output.append("")

    return "\n".join(output)


if __name__ == '__main__':
    """테스트 코드"""
    print("=== 팩터 스코어링 시스템 테스트 ===\n")

    # 샘플 데이터로 스코어링 테스트
    sample_data = pd.DataFrame({
        'code': ['005930', '000660', '035420'],
        'name': ['삼성전자', 'SK하이닉스', 'NAVER'],
        'sector': ['전기전자', '전기전자', '서비스업'],
        'per': [12.5, 8.3, 25.6],
        'pbr': [1.2, 0.9, 3.5],
        'roe': [15.3, 22.1, 18.7],
        'roa': [8.2, 12.5, 9.3],
        'debt_ratio': [45.2, 38.7, 25.1],
        'operating_margin': [12.5, 18.3, 15.6],
        'revenue_growth': [8.5, 15.2, 12.3],
        'net_profit_growth': [12.3, 25.6, 18.9],
        'volatility': 25.3
    })

    scorer = FactorScorer()

    print("1. 밸류 점수 계산")
    value_scored = scorer.calculate_value_score(sample_data)
    print(value_scored[['name', 'per', 'pbr', 'value_score']])
    print()

    print("2. 성장 점수 계산")
    growth_scored = scorer.calculate_growth_score(value_scored)
    print(growth_scored[['name', 'revenue_growth', 'net_profit_growth', 'growth_score']])
    print()

    print("3. 수익성 점수 계산")
    profit_scored = scorer.calculate_profitability_score(growth_scored)
    print(profit_scored[['name', 'roe', 'operating_margin', 'profitability_score']])
    print()

    print("4. 안정성 점수 계산")
    stability_scored = scorer.calculate_stability_score(profit_scored)
    print(stability_scored[['name', 'debt_ratio', 'stability_score']])
    print()

    print("5. 종합 점수 및 순위")
    final_scored = scorer.calculate_composite_score(stability_scored)
    ranked = scorer.rank_stocks(final_scored, top_n=3)
    print(ranked[['rank', 'name', 'composite_score', 'value_score', 'growth_score', 'profitability_score', 'stability_score']])
    print()

    print("✅ 팩터 스코어링 시스템 테스트 완료!")
