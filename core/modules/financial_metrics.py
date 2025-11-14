"""
재무 지표 계산 모듈

한국 주식 투자 분석을 위한 전통적인 재무 지표 계산 함수들을 제공합니다.
LLM이 아닌 Python으로 정확한 계산을 수행합니다.

주요 기능:
- PER, PBR, ROE, ROA 등 기본 재무 비율 계산
- 부채비율, 유동비율 계산
- 성장률 계산 (매출, 영업이익, 순이익)
- 수익성 지표 계산
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from core.utils.db_utils import get_db_connection


def calculate_basic_ratios(df: pd.DataFrame) -> pd.DataFrame:
    """
    기본 재무 비율 계산

    Args:
        df: 재무 데이터 DataFrame (columns: revenue, net_profit, total_assets, total_equity, total_debt, market_cap)

    Returns:
        계산된 지표가 추가된 DataFrame
    """
    result = df.copy()

    # ROE (자기자본이익률) = 순이익 / 자기자본 * 100
    result['roe'] = np.where(
        result['total_equity'] > 0,
        (result['net_profit'] / result['total_equity']) * 100,
        np.nan
    )

    # ROA (총자산이익률) = 순이익 / 총자산 * 100
    result['roa'] = np.where(
        result['total_assets'] > 0,
        (result['net_profit'] / result['total_assets']) * 100,
        np.nan
    )

    # 부채비율 = 부채 / 자기자본 * 100
    result['debt_ratio'] = np.where(
        result['total_equity'] > 0,
        (result['total_debt'] / result['total_equity']) * 100,
        np.nan
    )

    # PER (주가수익비율) = 시가총액 / 순이익
    if 'market_cap' in result.columns:
        result['per'] = np.where(
            result['net_profit'] > 0,
            result['market_cap'] / result['net_profit'],
            np.nan
        )

    # PBR (주가순자산비율) = 시가총액 / 자기자본
    if 'market_cap' in result.columns:
        result['pbr'] = np.where(
            result['total_equity'] > 0,
            result['market_cap'] / result['total_equity'],
            np.nan
        )

    return result


def calculate_profitability_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    수익성 지표 계산

    Args:
        df: 재무 데이터 DataFrame (columns: revenue, operating_profit, net_profit)

    Returns:
        수익성 지표가 추가된 DataFrame
    """
    result = df.copy()

    # 영업이익률 = 영업이익 / 매출 * 100
    result['operating_margin'] = np.where(
        result['revenue'] > 0,
        (result['operating_profit'] / result['revenue']) * 100,
        np.nan
    )

    # 순이익률 = 순이익 / 매출 * 100
    result['net_margin'] = np.where(
        result['revenue'] > 0,
        (result['net_profit'] / result['revenue']) * 100,
        np.nan
    )

    return result


def calculate_growth_rates(df: pd.DataFrame, periods: int = 4) -> pd.DataFrame:
    """
    성장률 계산 (YoY, QoQ)

    Args:
        df: 재무 데이터 DataFrame (시계열, code별로 정렬 필요)
        periods: 비교 기간 (4=YoY, 1=QoQ)

    Returns:
        성장률이 추가된 DataFrame
    """
    result = df.copy()

    # 종목별로 그룹화하여 성장률 계산
    for col in ['revenue', 'operating_profit', 'net_profit']:
        if col in result.columns:
            result[f'{col}_growth'] = result.groupby('code')[col].pct_change(periods) * 100

    return result


def calculate_valuation_scores(df: pd.DataFrame) -> pd.DataFrame:
    """
    밸류에이션 점수 계산 (0-10점)

    낮은 PER, PBR일수록 높은 점수

    Args:
        df: 재무 지표 DataFrame (per, pbr 컬럼 필요)

    Returns:
        밸류에이션 점수가 추가된 DataFrame
    """
    result = df.copy()

    # PER 점수 (0-5점)
    if 'per' in result.columns:
        result['per_score'] = np.select(
            [
                result['per'] <= 0,  # 적자
                result['per'] <= 5,
                result['per'] <= 10,
                result['per'] <= 15,
                result['per'] <= 20,
                result['per'] > 20
            ],
            [0, 5, 4, 3, 2, 1],
            default=0
        )

    # PBR 점수 (0-5점)
    if 'pbr' in result.columns:
        result['pbr_score'] = np.select(
            [
                result['pbr'] <= 0,  # 자본잠식
                result['pbr'] <= 0.5,
                result['pbr'] <= 1.0,
                result['pbr'] <= 1.5,
                result['pbr'] <= 2.0,
                result['pbr'] > 2.0
            ],
            [0, 5, 4, 3, 2, 1],
            default=0
        )

    return result


def calculate_quality_scores(df: pd.DataFrame) -> pd.DataFrame:
    """
    기업 품질 점수 계산 (0-10점)

    높은 ROE, 낮은 부채비율일수록 높은 점수

    Args:
        df: 재무 지표 DataFrame (roe, debt_ratio 컬럼 필요)

    Returns:
        품질 점수가 추가된 DataFrame
    """
    result = df.copy()

    # ROE 점수 (0-5점)
    if 'roe' in result.columns:
        result['roe_score'] = np.select(
            [
                result['roe'] <= 0,  # 적자
                result['roe'] <= 5,
                result['roe'] <= 10,
                result['roe'] <= 15,
                result['roe'] <= 20,
                result['roe'] > 20
            ],
            [0, 1, 2, 3, 4, 5],
            default=0
        )

    # 부채비율 점수 (0-5점)
    if 'debt_ratio' in result.columns:
        result['debt_score'] = np.select(
            [
                result['debt_ratio'] < 0,  # 자본잠식
                result['debt_ratio'] <= 50,
                result['debt_ratio'] <= 100,
                result['debt_ratio'] <= 150,
                result['debt_ratio'] <= 200,
                result['debt_ratio'] > 200
            ],
            [0, 5, 4, 3, 2, 1],
            default=0
        )

    return result


def get_financial_data_from_db(stock_codes: Optional[List[str]] = None) -> pd.DataFrame:
    """
    데이터베이스에서 재무 데이터 조회

    Args:
        stock_codes: 조회할 종목 코드 리스트 (None이면 전체)

    Returns:
        재무 데이터 DataFrame
    """
    conn = get_db_connection()

    query = """
    SELECT
        f.code,
        s.name,
        s.sector,
        f.year,
        f.quarter,
        f.revenue,
        f.operating_profit,
        f.net_profit,
        f.total_assets,
        f.total_equity,
        f.total_debt
    FROM financials f
    JOIN stocks s ON f.code = s.code
    """

    if stock_codes:
        placeholders = ','.join(['%s'] * len(stock_codes))
        query += f" WHERE f.code IN ({placeholders})"
        df = pd.read_sql_query(query, conn, params=stock_codes)
    else:
        df = pd.read_sql_query(query, conn)

    conn.close()

    # 시계열 정렬
    df = df.sort_values(['code', 'year', 'quarter'])

    return df


def get_latest_prices_from_db(stock_codes: Optional[List[str]] = None) -> pd.DataFrame:
    """
    데이터베이스에서 최신 가격 데이터 조회

    Args:
        stock_codes: 조회할 종목 코드 리스트 (None이면 전체)

    Returns:
        최신 가격 DataFrame
    """
    conn = get_db_connection()

    query = """
    SELECT DISTINCT ON (code)
        code,
        date,
        close as price,
        volume
    FROM prices
    """

    if stock_codes:
        placeholders = ','.join(['%s'] * len(stock_codes))
        query += f" WHERE code IN ({placeholders})"
        query += " ORDER BY code, date DESC"
        df = pd.read_sql_query(query, conn, params=stock_codes)
    else:
        query += " ORDER BY code, date DESC"
        df = pd.read_sql_query(query, conn)

    conn.close()

    return df


def calculate_market_cap(df: pd.DataFrame, share_counts: Optional[Dict[str, int]] = None) -> pd.DataFrame:
    """
    시가총액 계산

    Args:
        df: 가격 데이터 DataFrame (code, price 컬럼 필요)
        share_counts: 종목별 발행주식수 딕셔너리 {code: shares}

    Returns:
        시가총액이 추가된 DataFrame
    """
    result = df.copy()

    if share_counts:
        result['shares'] = result['code'].map(share_counts)
        result['market_cap'] = result['price'] * result['shares']
    else:
        # 발행주식수 정보가 없으면 None
        result['market_cap'] = np.nan

    return result


def analyze_stock_fundamentals(stock_code: str) -> Dict:
    """
    특정 종목의 종합 재무 분석

    Args:
        stock_code: 종목 코드

    Returns:
        분석 결과 딕셔너리
    """
    # 재무 데이터 조회
    financial_df = get_financial_data_from_db([stock_code])

    if financial_df.empty:
        return {
            'code': stock_code,
            'status': 'no_data',
            'message': '재무 데이터가 없습니다.'
        }

    # 최신 데이터
    latest = financial_df.iloc[-1]

    # 기본 비율 계산
    metrics = calculate_basic_ratios(financial_df)
    profitability = calculate_profitability_metrics(metrics)
    growth = calculate_growth_rates(profitability)

    # 최신 데이터
    latest_metrics = growth.iloc[-1]

    return {
        'code': stock_code,
        'name': latest['name'],
        'sector': latest['sector'],
        'year': int(latest['year']),
        'quarter': int(latest['quarter']),
        'revenue': int(latest['revenue']),
        'operating_profit': int(latest['operating_profit']),
        'net_profit': int(latest['net_profit']),
        'roe': round(float(latest_metrics['roe']), 2) if pd.notna(latest_metrics['roe']) else None,
        'roa': round(float(latest_metrics['roa']), 2) if pd.notna(latest_metrics['roa']) else None,
        'debt_ratio': round(float(latest_metrics['debt_ratio']), 2) if pd.notna(latest_metrics['debt_ratio']) else None,
        'operating_margin': round(float(latest_metrics['operating_margin']), 2) if pd.notna(latest_metrics['operating_margin']) else None,
        'net_margin': round(float(latest_metrics['net_margin']), 2) if pd.notna(latest_metrics['net_margin']) else None,
        'revenue_growth': round(float(latest_metrics['revenue_growth']), 2) if pd.notna(latest_metrics['revenue_growth']) else None,
        'profit_growth': round(float(latest_metrics['net_profit_growth']), 2) if pd.notna(latest_metrics['net_profit_growth']) else None,
        'status': 'success'
    }


if __name__ == '__main__':
    """테스트 코드"""
    print("=== 재무 지표 계산 모듈 테스트 ===\n")

    # 샘플 데이터로 테스트
    sample_data = pd.DataFrame({
        'code': ['005930', '005930', '005930', '005930'],
        'year': [2023, 2023, 2024, 2024],
        'quarter': [3, 4, 1, 2],
        'revenue': [67400000, 67800000, 71900000, 74000000],
        'operating_profit': [2820000, 6570000, 6640000, 10440000],
        'net_profit': [6270000, 6340000, 6610000, 10070000],
        'total_assets': [448200000, 452000000, 456000000, 460000000],
        'total_equity': [301300000, 305000000, 308000000, 312000000],
        'total_debt': [85000000, 84000000, 83000000, 82000000],
        'market_cap': [450000000, 450000000, 460000000, 470000000]
    })

    print("1. 기본 재무 비율 계산")
    ratios = calculate_basic_ratios(sample_data)
    print(ratios[['code', 'year', 'quarter', 'roe', 'roa', 'debt_ratio', 'per', 'pbr']].tail(2))
    print()

    print("2. 수익성 지표 계산")
    profitability = calculate_profitability_metrics(ratios)
    print(profitability[['code', 'year', 'quarter', 'operating_margin', 'net_margin']].tail(2))
    print()

    print("3. 성장률 계산 (YoY)")
    growth = calculate_growth_rates(profitability, periods=4)
    print(growth[['code', 'year', 'quarter', 'revenue_growth', 'net_profit_growth']].tail(2))
    print()

    print("4. 밸류에이션 점수")
    valuation = calculate_valuation_scores(growth)
    print(valuation[['code', 'year', 'quarter', 'per', 'per_score', 'pbr', 'pbr_score']].tail(2))
    print()

    print("5. 품질 점수")
    quality = calculate_quality_scores(valuation)
    print(quality[['code', 'year', 'quarter', 'roe', 'roe_score', 'debt_ratio', 'debt_score']].tail(2))
    print()

    print("✅ 재무 지표 계산 모듈 테스트 완료!")
