"""
포트폴리오 최적화 모듈

주요 기능:
- 동일가중 포트폴리오 생성
- 시가총액 가중 포트폴리오 생성
- 리스크 패리티 (Risk Parity) 포트폴리오
- 섹터 분산 체크
- 리밸런싱 제안
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from core.utils.db_utils import get_db_connection
from core.modules.risk_analysis import calculate_volatility, calculate_max_drawdown, calculate_sharpe_ratio


def get_stock_info(stock_codes: List[str]) -> pd.DataFrame:
    """
    종목 정보 조회

    Args:
        stock_codes: 종목 코드 리스트

    Returns:
        종목 정보 DataFrame (code, name, market, sector)
    """
    conn = get_db_connection()

    try:
        placeholders = ','.join(['%s'] * len(stock_codes))
        query = f"""
            SELECT code, name, market, sector
            FROM stocks
            WHERE code IN ({placeholders})
        """
        df = pd.read_sql(query, conn, params=stock_codes)
        return df

    finally:
        conn.close()


def get_latest_prices(stock_codes: List[str]) -> Dict[str, float]:
    """
    최신 가격 조회

    Args:
        stock_codes: 종목 코드 리스트

    Returns:
        {종목코드: 가격} 딕셔너리
    """
    conn = get_db_connection()

    try:
        prices = {}

        for code in stock_codes:
            query = """
                SELECT close
                FROM prices
                WHERE code = %s
                ORDER BY date DESC
                LIMIT 1
            """
            result = pd.read_sql(query, conn, params=(code,))

            if len(result) > 0:
                prices[code] = float(result['close'].iloc[0])

        return prices

    finally:
        conn.close()


def create_equal_weight_portfolio(stock_codes: List[str]) -> Dict:
    """
    동일가중 포트폴리오 생성

    Args:
        stock_codes: 종목 코드 리스트

    Returns:
        포트폴리오 정보
    """
    if len(stock_codes) == 0:
        return {
            'status': 'error',
            'message': '종목이 없습니다'
        }

    # 동일 비중 계산
    weight = 1.0 / len(stock_codes)
    weights = {code: weight for code in stock_codes}

    # 종목 정보 조회
    stock_info = get_stock_info(stock_codes)

    # 섹터 분산도 계산
    sector_distribution = stock_info['sector'].value_counts().to_dict() if len(stock_info) > 0 else {}

    return {
        'status': 'success',
        'method': '동일가중 (Equal Weight)',
        'stocks': stock_codes,
        'weights': weights,
        'num_stocks': len(stock_codes),
        'sector_distribution': sector_distribution
    }


def create_market_cap_weight_portfolio(stock_codes: List[str],
                                       market_caps: Optional[Dict[str, float]] = None) -> Dict:
    """
    시가총액 가중 포트폴리오 생성

    Args:
        stock_codes: 종목 코드 리스트
        market_caps: {종목코드: 시가총액} 딕셔너리 (옵션, None이면 가격 기준)

    Returns:
        포트폴리오 정보
    """
    if len(stock_codes) == 0:
        return {
            'status': 'error',
            'message': '종목이 없습니다'
        }

    # 시가총액이 없으면 가격 기준으로 가중치 계산
    if market_caps is None:
        market_caps = get_latest_prices(stock_codes)

    if len(market_caps) == 0:
        return {
            'status': 'error',
            'message': '가격 정보를 가져올 수 없습니다'
        }

    # 시가총액 합계
    total_cap = sum(market_caps.values())

    # 비중 계산
    weights = {code: market_caps.get(code, 0) / total_cap for code in stock_codes}

    # 종목 정보 조회
    stock_info = get_stock_info(stock_codes)
    sector_distribution = stock_info['sector'].value_counts().to_dict() if len(stock_info) > 0 else {}

    return {
        'status': 'success',
        'method': '시가총액 가중 (Market Cap Weight)',
        'stocks': stock_codes,
        'weights': weights,
        'num_stocks': len(stock_codes),
        'sector_distribution': sector_distribution,
        'market_caps': market_caps
    }


def create_risk_parity_portfolio(stock_codes: List[str], days: int = 252) -> Dict:
    """
    리스크 패리티 포트폴리오 생성
    각 종목이 포트폴리오 전체 리스크에 동일하게 기여하도록 비중 조정

    Args:
        stock_codes: 종목 코드 리스트
        days: 변동성 계산 기간

    Returns:
        포트폴리오 정보
    """
    if len(stock_codes) == 0:
        return {
            'status': 'error',
            'message': '종목이 없습니다'
        }

    conn = get_db_connection()

    try:
        # 각 종목의 변동성 계산
        volatilities = {}

        for code in stock_codes:
            query = """
                SELECT date, close
                FROM prices
                WHERE code = %s
                ORDER BY date DESC
                LIMIT %s
            """
            df = pd.read_sql(query, conn, params=(code, days))

            if len(df) < 10:
                continue

            df = df.sort_values('date')
            returns = df['close'].pct_change().dropna()
            vol = calculate_volatility(returns, annualize=True)

            volatilities[code] = vol

        if len(volatilities) == 0:
            return {
                'status': 'error',
                'message': '변동성 계산 실패'
            }

        # 변동성의 역수로 가중치 계산 (낮은 변동성 -> 높은 비중)
        inv_vols = {code: 1.0 / vol if vol > 0 else 0 for code, vol in volatilities.items()}
        total_inv_vol = sum(inv_vols.values())

        weights = {code: inv_vol / total_inv_vol for code, inv_vol in inv_vols.items()}

        # 종목 정보 조회
        stock_info = get_stock_info(stock_codes)
        sector_distribution = stock_info['sector'].value_counts().to_dict() if len(stock_info) > 0 else {}

        return {
            'status': 'success',
            'method': '리스크 패리티 (Risk Parity)',
            'stocks': list(weights.keys()),
            'weights': weights,
            'num_stocks': len(weights),
            'sector_distribution': sector_distribution,
            'volatilities': {k: round(v, 2) for k, v in volatilities.items()}
        }

    finally:
        conn.close()


def check_sector_diversification(stock_codes: List[str]) -> Dict:
    """
    섹터 분산도 체크

    Args:
        stock_codes: 종목 코드 리스트

    Returns:
        섹터 분산 분석 결과
    """
    stock_info = get_stock_info(stock_codes)

    if len(stock_info) == 0:
        return {
            'status': 'error',
            'message': '종목 정보를 가져올 수 없습니다'
        }

    # 섹터별 종목 수
    sector_counts = stock_info['sector'].value_counts().to_dict()
    num_sectors = len(sector_counts)

    # 집중도 계산 (HHI - Herfindahl-Hirschman Index)
    total_stocks = len(stock_info)
    sector_ratios = {sector: count / total_stocks for sector, count in sector_counts.items()}
    hhi = sum(ratio ** 2 for ratio in sector_ratios.values()) * 10000

    # 집중도 평가
    if hhi < 1500:
        concentration_level = '낮음 (분산 우수)'
    elif hhi < 2500:
        concentration_level = '보통'
    else:
        concentration_level = '높음 (분산 부족)'

    return {
        'status': 'success',
        'num_sectors': num_sectors,
        'sector_counts': sector_counts,
        'sector_ratios': {k: round(v * 100, 2) for k, v in sector_ratios.items()},
        'hhi': round(hhi, 2),
        'concentration_level': concentration_level,
        'recommendation': '3개 이상 섹터에 분산 투자 권장' if num_sectors < 3 else '양호한 섹터 분산'
    }


def suggest_rebalancing(current_weights: Dict[str, float],
                       target_weights: Dict[str, float],
                       threshold: float = 0.05) -> Dict:
    """
    리밸런싱 제안

    Args:
        current_weights: 현재 비중 {종목코드: 비중}
        target_weights: 목표 비중 {종목코드: 비중}
        threshold: 리밸런싱 임계값 (기본 5%)

    Returns:
        리밸런싱 제안
    """
    rebalancing_needed = []

    for code in target_weights.keys():
        current = current_weights.get(code, 0)
        target = target_weights.get(code, 0)
        diff = abs(current - target)

        if diff > threshold:
            action = '매수' if target > current else '매도'
            rebalancing_needed.append({
                'stock_code': code,
                'current_weight': round(current * 100, 2),
                'target_weight': round(target * 100, 2),
                'diff': round(diff * 100, 2),
                'action': action
            })

    # 리밸런싱 필요 여부
    needs_rebalancing = len(rebalancing_needed) > 0

    return {
        'status': 'success',
        'needs_rebalancing': needs_rebalancing,
        'threshold': threshold * 100,
        'rebalancing_actions': rebalancing_needed,
        'num_actions': len(rebalancing_needed),
        'message': f'{len(rebalancing_needed)}개 종목 리밸런싱 필요' if needs_rebalancing else '리밸런싱 불필요'
    }


def simulate_portfolio_performance(stock_codes: List[str],
                                   weights: Dict[str, float],
                                   days: int = 252) -> Dict:
    """
    포트폴리오 성과 시뮬레이션

    Args:
        stock_codes: 종목 코드 리스트
        weights: 비중 {종목코드: 비중}
        days: 시뮬레이션 기간

    Returns:
        성과 분석 결과
    """
    conn = get_db_connection()

    try:
        # 각 종목의 수익률 데이터 수집
        returns_dict = {}

        for code in stock_codes:
            query = """
                SELECT date, close
                FROM prices
                WHERE code = %s
                ORDER BY date DESC
                LIMIT %s
            """
            df = pd.read_sql(query, conn, params=(code, days))

            if len(df) < 10:
                continue

            df = df.sort_values('date').set_index('date')
            returns_dict[code] = df['close'].pct_change().dropna()

        if len(returns_dict) == 0:
            return {
                'status': 'error',
                'message': '수익률 데이터 없음'
            }

        # 수익률 DataFrame 생성
        returns_df = pd.DataFrame(returns_dict).dropna()

        # 포트폴리오 수익률 계산
        weight_list = [weights.get(code, 0) for code in returns_df.columns]
        portfolio_returns = (returns_df * weight_list).sum(axis=1)

        # 누적 수익률
        cumulative_returns = (1 + portfolio_returns).cumprod()
        total_return = (cumulative_returns.iloc[-1] - 1) * 100

        # 리스크 지표
        volatility = calculate_volatility(portfolio_returns)
        mdd_result = calculate_max_drawdown(cumulative_returns)
        sharpe = calculate_sharpe_ratio(portfolio_returns)

        # 연평균 수익률
        num_years = len(portfolio_returns) / 252
        annualized_return = ((1 + total_return / 100) ** (1 / num_years) - 1) * 100 if num_years > 0 else 0

        return {
            'status': 'success',
            'period_days': len(portfolio_returns),
            'total_return': round(total_return, 2),
            'annualized_return': round(annualized_return, 2),
            'volatility': round(volatility, 2),
            'max_drawdown': round(mdd_result['max_drawdown'], 2),
            'sharpe_ratio': round(sharpe, 3),
            'best_day': round(portfolio_returns.max() * 100, 2),
            'worst_day': round(portfolio_returns.min() * 100, 2)
        }

    finally:
        conn.close()


# 테스트 코드
if __name__ == "__main__":
    print("=== 포트폴리오 최적화 모듈 테스트 ===\n")

    test_stocks = ['005930', '000660', '035720']

    # 1. 동일가중 포트폴리오
    print("1. 동일가중 포트폴리오")
    print("-" * 50)
    equal_weight = create_equal_weight_portfolio(test_stocks)
    if equal_weight['status'] == 'success':
        print(f"✓ 방식: {equal_weight['method']}")
        print(f"  종목 수: {equal_weight['num_stocks']}")
        print(f"  비중: {equal_weight['weights']}")
        print(f"  섹터 분포: {equal_weight['sector_distribution']}")
    else:
        print(f"✗ 실패: {equal_weight['message']}")

    print("\n" + "="*70 + "\n")

    # 2. 리스크 패리티 포트폴리오
    print("2. 리스크 패리티 포트폴리오")
    print("-" * 50)
    risk_parity = create_risk_parity_portfolio(test_stocks)
    if risk_parity['status'] == 'success':
        print(f"✓ 방식: {risk_parity['method']}")
        print(f"  종목 수: {risk_parity['num_stocks']}")
        print(f"  비중: {risk_parity['weights']}")
        print(f"  변동성: {risk_parity['volatilities']}")
    else:
        print(f"✗ 실패: {risk_parity['message']}")

    print("\n" + "="*70 + "\n")

    # 3. 섹터 분산도 체크
    print("3. 섹터 분산도 체크")
    print("-" * 50)
    sector_check = check_sector_diversification(test_stocks)
    if sector_check['status'] == 'success':
        print(f"✓ 섹터 수: {sector_check['num_sectors']}")
        print(f"  섹터별 비중: {sector_check['sector_ratios']}")
        print(f"  집중도(HHI): {sector_check['hhi']}")
        print(f"  평가: {sector_check['concentration_level']}")
        print(f"  권장사항: {sector_check['recommendation']}")
    else:
        print(f"✗ 실패: {sector_check['message']}")

    print("\n" + "="*70 + "\n")

    # 4. 포트폴리오 성과 시뮬레이션
    print("4. 포트폴리오 성과 시뮬레이션 (동일가중)")
    print("-" * 50)
    if equal_weight['status'] == 'success':
        performance = simulate_portfolio_performance(test_stocks, equal_weight['weights'])
        if performance['status'] == 'success':
            print(f"✓ 분석 기간: {performance['period_days']}일")
            print(f"  총 수익률: {performance['total_return']}%")
            print(f"  연평균 수익률: {performance['annualized_return']}%")
            print(f"  변동성: {performance['volatility']}%")
            print(f"  최대 낙폭: {performance['max_drawdown']}%")
            print(f"  Sharpe Ratio: {performance['sharpe_ratio']}")
            print(f"  최고 수익일: {performance['best_day']}%")
            print(f"  최악 손실일: {performance['worst_day']}%")
        else:
            print(f"✗ 실패: {performance['message']}")

    print("\n=== 테스트 완료 ===")
