"""
기술적 지표 계산 모듈

가격 데이터를 기반으로 한 기술적 분석 지표를 계산합니다.
TA-Lib 설치가 어려운 경우를 대비해 pandas로 직접 구현합니다.

주요 기능:
- 이동평균 (SMA, EMA)
- RSI (Relative Strength Index)
- MACD (Moving Average Convergence Divergence)
- 볼린저 밴드
- 가격 모멘텀
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from core.utils.db_utils import get_db_connection


def calculate_sma(df: pd.DataFrame, column: str = 'close', period: int = 20) -> pd.Series:
    """
    단순 이동평균 (Simple Moving Average)

    Args:
        df: 가격 데이터 DataFrame
        column: 계산할 컬럼명
        period: 기간

    Returns:
        SMA Series
    """
    return df[column].rolling(window=period).mean()


def calculate_ema(df: pd.DataFrame, column: str = 'close', period: int = 20) -> pd.Series:
    """
    지수 이동평균 (Exponential Moving Average)

    Args:
        df: 가격 데이터 DataFrame
        column: 계산할 컬럼명
        period: 기간

    Returns:
        EMA Series
    """
    return df[column].ewm(span=period, adjust=False).mean()


def calculate_rsi(df: pd.DataFrame, column: str = 'close', period: int = 14) -> pd.Series:
    """
    RSI (Relative Strength Index)

    Args:
        df: 가격 데이터 DataFrame
        column: 계산할 컬럼명
        period: 기간 (일반적으로 14)

    Returns:
        RSI Series (0-100)
    """
    # 가격 변화
    delta = df[column].diff()

    # 상승분/하락분 분리
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    # 평균 상승분/하락분
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()

    # RS = 평균 상승분 / 평균 하락분
    rs = avg_gain / avg_loss

    # RSI = 100 - (100 / (1 + RS))
    rsi = 100 - (100 / (1 + rs))

    return rsi


def calculate_macd(
    df: pd.DataFrame,
    column: str = 'close',
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    MACD (Moving Average Convergence Divergence)

    Args:
        df: 가격 데이터 DataFrame
        column: 계산할 컬럼명
        fast_period: 빠른 EMA 기간
        slow_period: 느린 EMA 기간
        signal_period: 시그널 EMA 기간

    Returns:
        (MACD, Signal, Histogram) 튜플
    """
    # MACD 라인 = 빠른 EMA - 느린 EMA
    ema_fast = calculate_ema(df, column, fast_period)
    ema_slow = calculate_ema(df, column, slow_period)
    macd = ema_fast - ema_slow

    # 시그널 라인 = MACD의 EMA
    signal = macd.ewm(span=signal_period, adjust=False).mean()

    # 히스토그램 = MACD - Signal
    histogram = macd - signal

    return macd, signal, histogram


def calculate_bollinger_bands(
    df: pd.DataFrame,
    column: str = 'close',
    period: int = 20,
    std_dev: float = 2.0
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    볼린저 밴드 (Bollinger Bands)

    Args:
        df: 가격 데이터 DataFrame
        column: 계산할 컬럼명
        period: 기간
        std_dev: 표준편차 배수

    Returns:
        (Upper Band, Middle Band, Lower Band) 튜플
    """
    # 중간 밴드 = SMA
    middle_band = calculate_sma(df, column, period)

    # 표준편차
    std = df[column].rolling(window=period).std()

    # 상단 밴드 = 중간 밴드 + (표준편차 × 배수)
    upper_band = middle_band + (std * std_dev)

    # 하단 밴드 = 중간 밴드 - (표준편차 × 배수)
    lower_band = middle_band - (std * std_dev)

    return upper_band, middle_band, lower_band


def calculate_momentum(df: pd.DataFrame, column: str = 'close', period: int = 10) -> pd.Series:
    """
    모멘텀 (Momentum)

    현재 가격 - N일 전 가격

    Args:
        df: 가격 데이터 DataFrame
        column: 계산할 컬럼명
        period: 기간

    Returns:
        Momentum Series
    """
    return df[column] - df[column].shift(period)


def calculate_rate_of_change(df: pd.DataFrame, column: str = 'close', period: int = 10) -> pd.Series:
    """
    변화율 (Rate of Change, ROC)

    ((현재 가격 - N일 전 가격) / N일 전 가격) × 100

    Args:
        df: 가격 데이터 DataFrame
        column: 계산할 컬럼명
        period: 기간

    Returns:
        ROC Series (%)
    """
    return ((df[column] - df[column].shift(period)) / df[column].shift(period)) * 100


def calculate_volatility(df: pd.DataFrame, column: str = 'close', period: int = 20) -> pd.Series:
    """
    변동성 (Volatility)

    가격 변화율의 표준편차

    Args:
        df: 가격 데이터 DataFrame
        column: 계산할 컬럼명
        period: 기간

    Returns:
        Volatility Series (연율화)
    """
    returns = df[column].pct_change()
    volatility = returns.rolling(window=period).std() * np.sqrt(252) * 100

    return volatility


def get_price_data_from_db(stock_code: str, days: int = 120) -> pd.DataFrame:
    """
    데이터베이스에서 가격 데이터 조회

    Args:
        stock_code: 종목 코드
        days: 조회 기간 (일수)

    Returns:
        가격 데이터 DataFrame
    """
    conn = get_db_connection()

    query = """
    SELECT date, open, high, low, close, volume
    FROM prices
    WHERE code = %s
        AND date >= CURRENT_DATE - INTERVAL '%s days'
    ORDER BY date ASC
    """

    df = pd.read_sql_query(query, conn, params=(stock_code, days))
    conn.close()

    return df


def analyze_technical_indicators(stock_code: str, days: int = 120) -> Dict:
    """
    특정 종목의 기술적 지표 분석

    Args:
        stock_code: 종목 코드
        days: 분석 기간 (일수)

    Returns:
        분석 결과 딕셔너리
    """
    # 가격 데이터 조회
    df = get_price_data_from_db(stock_code, days)

    if df.empty:
        return {
            'code': stock_code,
            'status': 'no_data',
            'message': '가격 데이터가 없습니다.'
        }

    # 기술적 지표 계산
    df['sma_20'] = calculate_sma(df, 'close', 20)
    df['sma_60'] = calculate_sma(df, 'close', 60)
    df['ema_20'] = calculate_ema(df, 'close', 20)
    df['rsi'] = calculate_rsi(df, 'close', 14)

    macd, signal, histogram = calculate_macd(df)
    df['macd'] = macd
    df['macd_signal'] = signal
    df['macd_histogram'] = histogram

    upper_band, middle_band, lower_band = calculate_bollinger_bands(df)
    df['bb_upper'] = upper_band
    df['bb_middle'] = middle_band
    df['bb_lower'] = lower_band

    df['momentum'] = calculate_momentum(df, 'close', 10)
    df['roc'] = calculate_rate_of_change(df, 'close', 10)
    df['volatility'] = calculate_volatility(df, 'close', 20)

    # 최신 데이터
    latest = df.iloc[-1]

    # 기술적 시그널 판단
    signals = []

    # RSI 시그널
    if pd.notna(latest['rsi']):
        if latest['rsi'] < 30:
            signals.append("RSI 과매도 (< 30)")
        elif latest['rsi'] > 70:
            signals.append("RSI 과매수 (> 70)")

    # 이동평균 시그널
    if pd.notna(latest['sma_20']) and pd.notna(latest['sma_60']):
        if latest['close'] > latest['sma_20'] > latest['sma_60']:
            signals.append("골든크로스 (상승 추세)")
        elif latest['close'] < latest['sma_20'] < latest['sma_60']:
            signals.append("데드크로스 (하락 추세)")

    # MACD 시그널
    if pd.notna(latest['macd']) and pd.notna(latest['macd_signal']):
        if latest['macd'] > latest['macd_signal'] and latest['macd_histogram'] > 0:
            signals.append("MACD 매수 신호")
        elif latest['macd'] < latest['macd_signal'] and latest['macd_histogram'] < 0:
            signals.append("MACD 매도 신호")

    # 볼린저 밴드 시그널
    if pd.notna(latest['bb_upper']) and pd.notna(latest['bb_lower']):
        if latest['close'] > latest['bb_upper']:
            signals.append("볼린저 밴드 상단 돌파")
        elif latest['close'] < latest['bb_lower']:
            signals.append("볼린저 밴드 하단 이탈")

    return {
        'code': stock_code,
        'date': str(latest['date']),
        'close': float(latest['close']),
        'sma_20': round(float(latest['sma_20']), 2) if pd.notna(latest['sma_20']) else None,
        'sma_60': round(float(latest['sma_60']), 2) if pd.notna(latest['sma_60']) else None,
        'ema_20': round(float(latest['ema_20']), 2) if pd.notna(latest['ema_20']) else None,
        'rsi': round(float(latest['rsi']), 2) if pd.notna(latest['rsi']) else None,
        'macd': round(float(latest['macd']), 4) if pd.notna(latest['macd']) else None,
        'macd_signal': round(float(latest['macd_signal']), 4) if pd.notna(latest['macd_signal']) else None,
        'macd_histogram': round(float(latest['macd_histogram']), 4) if pd.notna(latest['macd_histogram']) else None,
        'bb_upper': round(float(latest['bb_upper']), 2) if pd.notna(latest['bb_upper']) else None,
        'bb_middle': round(float(latest['bb_middle']), 2) if pd.notna(latest['bb_middle']) else None,
        'bb_lower': round(float(latest['bb_lower']), 2) if pd.notna(latest['bb_lower']) else None,
        'volatility': round(float(latest['volatility']), 2) if pd.notna(latest['volatility']) else None,
        'signals': signals,
        'status': 'success'
    }


def get_technical_signals(stock_codes: List[str], days: int = 120) -> pd.DataFrame:
    """
    여러 종목의 기술적 시그널 조회

    Args:
        stock_codes: 종목 코드 리스트
        days: 분석 기간

    Returns:
        시그널 DataFrame
    """
    results = []

    for code in stock_codes:
        analysis = analyze_technical_indicators(code, days)
        if analysis['status'] == 'success':
            results.append({
                'code': code,
                'rsi': analysis['rsi'],
                'macd_signal': 'buy' if analysis['macd'] and analysis['macd'] > analysis['macd_signal'] else 'sell',
                'trend': 'up' if analysis['close'] > analysis['sma_20'] else 'down',
                'volatility': analysis['volatility'],
                'signals': ', '.join(analysis['signals']) if analysis['signals'] else 'None'
            })

    return pd.DataFrame(results)


if __name__ == '__main__':
    """테스트 코드"""
    print("=== 기술적 지표 계산 모듈 테스트 ===\n")

    # 샘플 데이터 생성
    dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
    np.random.seed(42)

    # 가상의 주가 데이터 (랜덤 워크)
    prices = 50000 + np.cumsum(np.random.randn(100) * 500)

    sample_data = pd.DataFrame({
        'date': dates,
        'open': prices + np.random.randn(100) * 100,
        'high': prices + np.abs(np.random.randn(100) * 200),
        'low': prices - np.abs(np.random.randn(100) * 200),
        'close': prices,
        'volume': np.random.randint(1000000, 10000000, 100)
    })

    print("1. 이동평균 계산")
    sample_data['sma_20'] = calculate_sma(sample_data, 'close', 20)
    sample_data['ema_20'] = calculate_ema(sample_data, 'close', 20)
    print(sample_data[['date', 'close', 'sma_20', 'ema_20']].tail(5))
    print()

    print("2. RSI 계산")
    sample_data['rsi'] = calculate_rsi(sample_data, 'close', 14)
    print(sample_data[['date', 'close', 'rsi']].tail(5))
    print()

    print("3. MACD 계산")
    macd, signal, histogram = calculate_macd(sample_data)
    sample_data['macd'] = macd
    sample_data['macd_signal'] = signal
    sample_data['macd_histogram'] = histogram
    print(sample_data[['date', 'macd', 'macd_signal', 'macd_histogram']].tail(5))
    print()

    print("4. 볼린저 밴드 계산")
    upper, middle, lower = calculate_bollinger_bands(sample_data)
    sample_data['bb_upper'] = upper
    sample_data['bb_middle'] = middle
    sample_data['bb_lower'] = lower
    print(sample_data[['date', 'close', 'bb_upper', 'bb_middle', 'bb_lower']].tail(5))
    print()

    print("5. 변동성 계산")
    sample_data['volatility'] = calculate_volatility(sample_data, 'close', 20)
    print(sample_data[['date', 'close', 'volatility']].tail(5))
    print()

    print("✅ 기술적 지표 계산 모듈 테스트 완료!")
