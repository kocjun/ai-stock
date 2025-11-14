"""
리스크 분석 모듈

주요 기능:
- 변동성 계산 (표준편차, 연율화)
- MDD (Maximum Drawdown) 계산
- VaR (Value at Risk) 계산
- Sharpe Ratio 계산
- 종목별 리스크 점수 산출
"""

import numpy as np
import pandas as pd
from typing import Dict, Optional, Tuple
from core.utils.db_utils import get_db_connection


def calculate_volatility(returns: pd.Series, annualize: bool = True) -> float:
    """
    변동성(표준편차) 계산

    Args:
        returns: 수익률 시계열
        annualize: 연율화 여부 (기본값: True)

    Returns:
        변동성 (%)
    """
    if len(returns) < 2:
        return 0.0

    volatility = returns.std()

    if annualize:
        # 일간 데이터 기준 연율화 (252 거래일)
        volatility = volatility * np.sqrt(252)

    return volatility * 100  # 백분율 변환


def calculate_max_drawdown(prices: pd.Series) -> Dict[str, float]:
    """
    최대 낙폭(MDD) 계산

    Args:
        prices: 가격 시계열

    Returns:
        {
            'max_drawdown': MDD (%),
            'peak_date': 고점 날짜,
            'trough_date': 저점 날짜
        }
    """
    if len(prices) < 2:
        return {
            'max_drawdown': 0.0,
            'peak_date': None,
            'trough_date': None
        }

    # 누적 최대값 계산
    cumulative_max = prices.expanding().max()

    # Drawdown 계산
    drawdown = (prices - cumulative_max) / cumulative_max

    # 최대 낙폭
    max_drawdown = drawdown.min()

    # MDD 발생 시점
    trough_idx = drawdown.idxmin()
    peak_idx = prices[:trough_idx].idxmax() if trough_idx else None

    return {
        'max_drawdown': max_drawdown * 100,  # 백분율
        'peak_date': peak_idx,
        'trough_date': trough_idx
    }


def calculate_var(returns: pd.Series, confidence_level: float = 0.95) -> float:
    """
    VaR (Value at Risk) 계산 - 역사적 시뮬레이션 방식

    Args:
        returns: 수익률 시계열
        confidence_level: 신뢰수준 (기본값: 95%)

    Returns:
        VaR (%)
    """
    if len(returns) < 10:
        return 0.0

    # 역사적 VaR (Historical VaR)
    var = np.percentile(returns, (1 - confidence_level) * 100)

    return var * 100  # 백분율 변환


def calculate_sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.02) -> float:
    """
    Sharpe Ratio 계산

    Args:
        returns: 수익률 시계열
        risk_free_rate: 무위험 수익률 (연율, 기본값: 2%)

    Returns:
        Sharpe Ratio
    """
    if len(returns) < 2:
        return 0.0

    # 평균 수익률 (연율화)
    avg_return = returns.mean() * 252

    # 변동성 (연율화)
    volatility = returns.std() * np.sqrt(252)

    if volatility == 0:
        return 0.0

    # Sharpe Ratio
    sharpe = (avg_return - risk_free_rate) / volatility

    return sharpe


def calculate_beta(stock_returns: pd.Series, market_returns: pd.Series) -> float:
    """
    베타(Beta) 계산 - 시장 대비 민감도

    Args:
        stock_returns: 종목 수익률
        market_returns: 시장(벤치마크) 수익률

    Returns:
        Beta
    """
    if len(stock_returns) < 2 or len(market_returns) < 2:
        return 1.0

    # 공통 날짜 추출
    aligned = pd.DataFrame({
        'stock': stock_returns,
        'market': market_returns
    }).dropna()

    if len(aligned) < 2:
        return 1.0

    # 공분산 / 시장 분산
    covariance = aligned['stock'].cov(aligned['market'])
    market_variance = aligned['market'].var()

    if market_variance == 0:
        return 1.0

    beta = covariance / market_variance

    return beta


def calculate_downside_deviation(returns: pd.Series, target_return: float = 0.0) -> float:
    """
    하방 편차(Downside Deviation) 계산

    Args:
        returns: 수익률 시계열
        target_return: 목표 수익률 (기본값: 0)

    Returns:
        Downside Deviation (연율화, %)
    """
    if len(returns) < 2:
        return 0.0

    # 목표 수익률 이하의 수익률만 추출
    downside_returns = returns[returns < target_return]

    if len(downside_returns) == 0:
        return 0.0

    # 하방 편차 계산
    downside_dev = np.sqrt(((downside_returns - target_return) ** 2).mean())

    # 연율화
    downside_dev = downside_dev * np.sqrt(252)

    return downside_dev * 100


def calculate_sortino_ratio(returns: pd.Series,
                            target_return: float = 0.0,
                            risk_free_rate: float = 0.02) -> float:
    """
    Sortino Ratio 계산 - Sharpe Ratio의 개선 버전 (하방 리스크만 고려)

    Args:
        returns: 수익률 시계열
        target_return: 목표 수익률
        risk_free_rate: 무위험 수익률 (연율)

    Returns:
        Sortino Ratio
    """
    if len(returns) < 2:
        return 0.0

    # 평균 수익률 (연율화)
    avg_return = returns.mean() * 252

    # 하방 편차
    downside_dev = calculate_downside_deviation(returns, target_return) / 100

    if downside_dev == 0:
        return 0.0

    sortino = (avg_return - risk_free_rate) / downside_dev

    return sortino


def calculate_win_rate(returns: pd.Series) -> float:
    """
    승률 계산 (양의 수익률 비율)

    Args:
        returns: 수익률 시계열

    Returns:
        승률 (%)
    """
    if len(returns) == 0:
        return 0.0

    win_rate = (returns > 0).sum() / len(returns)

    return win_rate * 100


def calculate_risk_score(stock_code: str, days: int = 252) -> Dict:
    """
    종목별 종합 리스크 점수 계산

    Args:
        stock_code: 종목 코드
        days: 분석 기간 (일)

    Returns:
        리스크 분석 결과 딕셔너리
    """
    conn = get_db_connection()

    try:
        # 가격 데이터 조회
        query = """
            SELECT date, close
            FROM prices
            WHERE code = %s
            ORDER BY date DESC
            LIMIT %s
        """
        df = pd.read_sql(query, conn, params=(stock_code, days))

        if len(df) < 10:
            return {
                'status': 'error',
                'message': '데이터 부족 (최소 10일 필요)'
            }

        # 날짜 순 정렬
        df = df.sort_values('date')
        df = df.set_index('date')

        # 수익률 계산
        returns = df['close'].pct_change().dropna()

        # 각종 리스크 지표 계산
        volatility = calculate_volatility(returns)
        mdd_result = calculate_max_drawdown(df['close'])
        var_95 = calculate_var(returns, 0.95)
        sharpe = calculate_sharpe_ratio(returns)
        downside_dev = calculate_downside_deviation(returns)
        sortino = calculate_sortino_ratio(returns)
        win_rate = calculate_win_rate(returns)

        # 종합 리스크 점수 (0-10, 높을수록 위험)
        # 변동성 기준 점수
        vol_score = min(volatility / 5, 10)  # 50% 변동성 = 10점

        # MDD 기준 점수
        mdd_score = min(abs(mdd_result['max_drawdown']) / 5, 10)  # -50% MDD = 10점

        # VaR 기준 점수
        var_score = min(abs(var_95) / 3, 10)  # -30% VaR = 10점

        # 종합 점수 (가중평균)
        risk_score = (vol_score * 0.3 + mdd_score * 0.4 + var_score * 0.3)

        # 리스크 등급
        if risk_score < 3:
            risk_grade = '낮음'
        elif risk_score < 6:
            risk_grade = '보통'
        elif risk_score < 8:
            risk_grade = '높음'
        else:
            risk_grade = '매우 높음'

        return {
            'status': 'success',
            'stock_code': stock_code,
            'period_days': len(df),
            'volatility': round(volatility, 2),
            'max_drawdown': round(mdd_result['max_drawdown'], 2),
            'var_95': round(var_95, 2),
            'sharpe_ratio': round(sharpe, 3),
            'downside_deviation': round(downside_dev, 2),
            'sortino_ratio': round(sortino, 3),
            'win_rate': round(win_rate, 2),
            'risk_score': round(risk_score, 2),
            'risk_grade': risk_grade,
            'peak_date': str(mdd_result['peak_date']) if mdd_result['peak_date'] else None,
            'trough_date': str(mdd_result['trough_date']) if mdd_result['trough_date'] else None
        }

    except Exception as e:
        return {
            'status': 'error',
            'message': str(e)
        }

    finally:
        conn.close()


def analyze_portfolio_risk(stock_codes: list, weights: Optional[list] = None, days: int = 252) -> Dict:
    """
    포트폴리오 리스크 분석

    Args:
        stock_codes: 종목 코드 리스트
        weights: 비중 리스트 (합계 1.0, None이면 동일가중)
        days: 분석 기간

    Returns:
        포트폴리오 리스크 분석 결과
    """
    if weights is None:
        weights = [1.0 / len(stock_codes)] * len(stock_codes)

    if len(stock_codes) != len(weights):
        return {
            'status': 'error',
            'message': '종목 수와 비중 수가 일치하지 않습니다'
        }

    if abs(sum(weights) - 1.0) > 0.01:
        return {
            'status': 'error',
            'message': '비중 합계가 1.0이 아닙니다'
        }

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
                'message': '유효한 데이터가 없습니다'
            }

        # 수익률 DataFrame 생성
        returns_df = pd.DataFrame(returns_dict).dropna()

        # 포트폴리오 수익률 계산
        portfolio_returns = (returns_df * weights).sum(axis=1)

        # 포트폴리오 리스크 지표
        portfolio_volatility = calculate_volatility(portfolio_returns)
        portfolio_mdd = calculate_max_drawdown((1 + portfolio_returns).cumprod())
        portfolio_sharpe = calculate_sharpe_ratio(portfolio_returns)
        portfolio_var = calculate_var(portfolio_returns)

        # 상관계수 행렬
        correlation_matrix = returns_df.corr()
        avg_correlation = correlation_matrix.values[np.triu_indices_from(correlation_matrix.values, k=1)].mean()

        # 분산 효과 (동일가중 vs 최적 포트폴리오)
        individual_vol = returns_df.std().mean() * np.sqrt(252) * 100
        diversification_ratio = portfolio_volatility / individual_vol if individual_vol > 0 else 1.0

        return {
            'status': 'success',
            'portfolio_size': len(stock_codes),
            'period_days': len(portfolio_returns),
            'portfolio_volatility': round(portfolio_volatility, 2),
            'portfolio_max_drawdown': round(portfolio_mdd['max_drawdown'], 2),
            'portfolio_sharpe_ratio': round(portfolio_sharpe, 3),
            'portfolio_var_95': round(portfolio_var, 2),
            'average_correlation': round(avg_correlation, 3),
            'diversification_ratio': round(diversification_ratio, 3),
            'stocks': stock_codes,
            'weights': [round(w, 4) for w in weights]
        }

    except Exception as e:
        return {
            'status': 'error',
            'message': str(e)
        }

    finally:
        conn.close()


# 테스트 코드
if __name__ == "__main__":
    print("=== 리스크 분석 모듈 테스트 ===\n")

    # 1. 단일 종목 리스크 분석
    print("1. 단일 종목 리스크 분석 (005930 - 삼성전자)")
    result = calculate_risk_score('005930', days=252)

    if result['status'] == 'success':
        print(f"✓ 분석 기간: {result['period_days']}일")
        print(f"  변동성: {result['volatility']}%")
        print(f"  최대 낙폭(MDD): {result['max_drawdown']}%")
        print(f"  VaR(95%): {result['var_95']}%")
        print(f"  Sharpe Ratio: {result['sharpe_ratio']}")
        print(f"  Sortino Ratio: {result['sortino_ratio']}")
        print(f"  하방 편차: {result['downside_deviation']}%")
        print(f"  승률: {result['win_rate']}%")
        print(f"  리스크 점수: {result['risk_score']}/10")
        print(f"  리스크 등급: {result['risk_grade']}")
    else:
        print(f"✗ 실패: {result['message']}")

    print("\n" + "="*50 + "\n")

    # 2. 포트폴리오 리스크 분석
    print("2. 포트폴리오 리스크 분석")
    portfolio_result = analyze_portfolio_risk(
        stock_codes=['005930', '000660', '035720'],
        weights=[0.4, 0.3, 0.3],
        days=252
    )

    if portfolio_result['status'] == 'success':
        print(f"✓ 포트폴리오 구성: {portfolio_result['portfolio_size']}개 종목")
        print(f"  종목: {portfolio_result['stocks']}")
        print(f"  비중: {portfolio_result['weights']}")
        print(f"  변동성: {portfolio_result['portfolio_volatility']}%")
        print(f"  최대 낙폭: {portfolio_result['portfolio_max_drawdown']}%")
        print(f"  Sharpe Ratio: {portfolio_result['portfolio_sharpe_ratio']}")
        print(f"  VaR(95%): {portfolio_result['portfolio_var_95']}%")
        print(f"  평균 상관계수: {portfolio_result['average_correlation']}")
        print(f"  분산 효과: {portfolio_result['diversification_ratio']:.2f}x")
    else:
        print(f"✗ 실패: {portfolio_result['message']}")

    print("\n=== 테스트 완료 ===")
