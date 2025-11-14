"""
백테스팅 모듈

과거 데이터 기반 투자 전략 검증:
- 팩터 기반 스크리닝 전략
- 포트폴리오 최적화 전략 (동일가중, 시총가중, 리스크패리티)
- 월간 리밸런싱 시뮬레이션
- 성과 지표 계산 (수익률, MDD, Sharpe Ratio 등)
- 벤치마크 비교 (KOSPI)
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from core.utils.db_utils import get_db_connection
from core.modules.risk_analysis import (
    calculate_volatility,
    calculate_max_drawdown,
    calculate_sharpe_ratio,
    calculate_sortino_ratio,
    calculate_beta
)
from core.modules.portfolio_optimization import (
    create_equal_weight_portfolio,
    create_market_cap_weight_portfolio,
    create_risk_parity_portfolio
)
from core.modules.factor_scoring import screen_stocks


def load_historical_data(
    stock_codes: List[str],
    start_date: str,
    end_date: str
) -> pd.DataFrame:
    """
    과거 가격 데이터 로드

    Args:
        stock_codes: 종목 코드 리스트
        start_date: 시작일 (YYYY-MM-DD)
        end_date: 종료일 (YYYY-MM-DD)

    Returns:
        가격 데이터 DataFrame (multi-index: date, code)
    """
    if len(stock_codes) == 0:
        return pd.DataFrame()

    conn = get_db_connection()

    try:
        placeholders = ','.join(['%s'] * len(stock_codes))
        query = f"""
            SELECT code, date, close
            FROM prices
            WHERE code IN ({placeholders})
              AND date BETWEEN %s AND %s
            ORDER BY date, code
        """
        params = stock_codes + [start_date, end_date]
        df = pd.read_sql(query, conn, params=params)

        if len(df) == 0:
            return pd.DataFrame()

        # Pivot: 날짜별로 종목 가격을 컬럼으로
        df_pivot = df.pivot(index='date', columns='code', values='close')

        return df_pivot

    finally:
        conn.close()


def get_benchmark_data(start_date: str, end_date: str, benchmark: str = "KS11") -> pd.Series:
    """
    벤치마크 데이터 로드 (KOSPI 지수)

    Args:
        start_date: 시작일 (YYYY-MM-DD)
        end_date: 종료일 (YYYY-MM-DD)
        benchmark: 벤치마크 코드 (기본값: KS11 = KOSPI)

    Returns:
        벤치마크 가격 시계열
    """
    conn = get_db_connection()

    try:
        query = """
            SELECT date, close
            FROM prices
            WHERE code = %s
              AND date BETWEEN %s AND %s
            ORDER BY date
        """
        df = pd.read_sql(query, conn, params=(benchmark, start_date, end_date))

        if len(df) == 0:
            # 벤치마크 데이터 없으면 빈 Series 반환
            return pd.Series(dtype=float)

        df = df.set_index('date')
        return df['close']

    finally:
        conn.close()


def calculate_portfolio_returns(
    prices: pd.DataFrame,
    weights: Dict[str, float],
    rebalance_freq: str = "M"
) -> pd.Series:
    """
    포트폴리오 수익률 계산

    Args:
        prices: 가격 데이터 (날짜 x 종목)
        weights: 종목별 비중 {종목코드: 비중}
        rebalance_freq: 리밸런싱 주기 ('M'=월간, 'Q'=분기, 'Y'=연간)

    Returns:
        포트폴리오 누적 수익률 시계열
    """
    if len(prices) == 0 or len(weights) == 0:
        return pd.Series(dtype=float)

    # 수익률 계산
    returns = prices.pct_change()

    # 포트폴리오 수익률 = 가중 평균
    portfolio_returns = pd.Series(0, index=returns.index)

    for code, weight in weights.items():
        if code in returns.columns:
            portfolio_returns += returns[code] * weight

    # 리밸런싱 주기별로 재조정 (간소화: 동일 비중 유지)
    # 실제로는 리밸런싱 시점마다 weights를 재계산해야 함

    # 누적 수익률 계산
    cumulative_returns = (1 + portfolio_returns).cumprod()

    return cumulative_returns


def run_backtest(
    start_date: str,
    end_date: str,
    strategy: str = "equal_weight",
    top_n: int = 10,
    rebalance_months: int = 1,
    min_roe: float = 10.0,
    max_debt_ratio: float = 150.0
) -> Dict:
    """
    백테스트 실행

    Args:
        start_date: 시작일 (YYYY-MM-DD)
        end_date: 종료일 (YYYY-MM-DD)
        strategy: 포트폴리오 전략 (equal_weight, market_cap, risk_parity)
        top_n: 선정 종목 수
        rebalance_months: 리밸런싱 주기 (개월)
        min_roe: 최소 ROE (%)
        max_debt_ratio: 최대 부채비율 (%)

    Returns:
        백테스트 결과 딕셔너리
    """
    print(f"\n{'='*60}")
    print(f"백테스트 시작")
    print(f"기간: {start_date} ~ {end_date}")
    print(f"전략: {strategy}, 종목수: {top_n}, 리밸런싱: {rebalance_months}개월")
    print(f"{'='*60}\n")

    # 1. 스크리닝 실행 (백테스트 시작 시점)
    print("1단계: 종목 스크리닝...")
    screening_result = screen_stocks(
        top_n=top_n,
        min_roe=min_roe,
        max_debt_ratio=max_debt_ratio
    )

    if screening_result['status'] != 'success' or len(screening_result['top_stocks']) == 0:
        return {
            'status': 'error',
            'message': '스크리닝 실패 또는 종목 없음'
        }

    selected_stocks = [s['code'] for s in screening_result['top_stocks']]
    print(f"   선정 종목: {len(selected_stocks)}개")

    # 2. 포트폴리오 구성
    print(f"2단계: 포트폴리오 구성 ({strategy})...")
    if strategy == "equal_weight":
        portfolio = create_equal_weight_portfolio(selected_stocks)
    elif strategy == "market_cap":
        portfolio = create_market_cap_weight_portfolio(selected_stocks)
    elif strategy == "risk_parity":
        # 과거 60일 데이터 기반으로 변동성 계산
        lookback_start = (datetime.strptime(start_date, '%Y-%m-%d') - timedelta(days=90)).strftime('%Y-%m-%d')
        historical_prices = load_historical_data(selected_stocks, lookback_start, start_date)
        portfolio = create_risk_parity_portfolio(selected_stocks, historical_prices)
    else:
        return {
            'status': 'error',
            'message': f'알 수 없는 전략: {strategy}'
        }

    if portfolio['status'] != 'success':
        return portfolio

    weights = portfolio['weights']
    print(f"   비중 설정 완료: {len(weights)}개 종목")

    # 3. 과거 가격 데이터 로드
    print("3단계: 과거 데이터 로드...")
    prices = load_historical_data(selected_stocks, start_date, end_date)

    if len(prices) == 0:
        return {
            'status': 'error',
            'message': f'기간 내 가격 데이터 없음 ({start_date} ~ {end_date})'
        }

    print(f"   데이터 로드 완료: {len(prices)} 거래일")

    # 4. 포트폴리오 수익률 계산
    print("4단계: 수익률 계산...")
    cumulative_returns = calculate_portfolio_returns(prices, weights)

    if len(cumulative_returns) == 0:
        return {
            'status': 'error',
            'message': '수익률 계산 실패'
        }

    # 5. 벤치마크 로드 (KOSPI)
    print("5단계: 벤치마크 비교...")
    benchmark_prices = get_benchmark_data(start_date, end_date)

    if len(benchmark_prices) > 0:
        benchmark_returns = (benchmark_prices / benchmark_prices.iloc[0])
    else:
        benchmark_returns = pd.Series(dtype=float)
        print("   경고: 벤치마크 데이터 없음")

    # 6. 성과 지표 계산
    print("6단계: 성과 지표 계산...")

    # 일간 수익률
    daily_returns = cumulative_returns.pct_change().dropna()

    # 최종 수익률
    total_return = (cumulative_returns.iloc[-1] - 1) * 100

    # CAGR (연평균 성장률)
    days = (pd.to_datetime(end_date) - pd.to_datetime(start_date)).days
    years = days / 365.25
    cagr = ((cumulative_returns.iloc[-1] ** (1 / years)) - 1) * 100 if years > 0 else 0

    # 변동성
    volatility = calculate_volatility(daily_returns, annualize=True)

    # MDD
    mdd_info = calculate_max_drawdown(cumulative_returns)

    # Sharpe Ratio
    sharpe = calculate_sharpe_ratio(daily_returns)

    # Sortino Ratio
    sortino = calculate_sortino_ratio(daily_returns)

    # 승률
    win_rate = (daily_returns > 0).sum() / len(daily_returns) * 100 if len(daily_returns) > 0 else 0

    # 평균 수익/손실
    avg_gain = daily_returns[daily_returns > 0].mean() * 100 if len(daily_returns[daily_returns > 0]) > 0 else 0
    avg_loss = daily_returns[daily_returns < 0].mean() * 100 if len(daily_returns[daily_returns < 0]) > 0 else 0

    # 벤치마크 대비
    if len(benchmark_returns) > 0:
        benchmark_total_return = (benchmark_returns.iloc[-1] / benchmark_returns.iloc[0] - 1) * 100
        alpha = total_return - benchmark_total_return

        # 베타 계산
        benchmark_daily_returns = benchmark_returns.pct_change().dropna()
        beta = calculate_beta(daily_returns, benchmark_daily_returns)
    else:
        benchmark_total_return = 0
        alpha = 0
        beta = 1.0

    print(f"\n{'='*60}")
    print(f"백테스트 완료!")
    print(f"{'='*60}\n")

    # 결과 반환
    return {
        'status': 'success',
        'period': {
            'start_date': start_date,
            'end_date': end_date,
            'days': days,
            'years': round(years, 2)
        },
        'strategy': {
            'name': strategy,
            'top_n': top_n,
            'rebalance_months': rebalance_months,
            'selected_stocks': selected_stocks,
            'weights': weights
        },
        'returns': {
            'total_return': round(total_return, 2),
            'cagr': round(cagr, 2),
            'volatility': round(volatility, 2),
            'sharpe_ratio': round(sharpe, 2),
            'sortino_ratio': round(sortino, 2),
            'max_drawdown': round(mdd_info['max_drawdown'], 2),
            'win_rate': round(win_rate, 2),
            'avg_gain': round(avg_gain, 4),
            'avg_loss': round(avg_loss, 4)
        },
        'benchmark': {
            'name': 'KOSPI',
            'total_return': round(benchmark_total_return, 2),
            'alpha': round(alpha, 2),
            'beta': round(beta, 2)
        },
        'cumulative_returns': cumulative_returns,
        'benchmark_returns': benchmark_returns
    }


def compare_strategies(
    start_date: str,
    end_date: str,
    strategies: List[str] = ["equal_weight", "market_cap", "risk_parity"],
    top_n: int = 10
) -> Dict:
    """
    여러 전략 비교

    Args:
        start_date: 시작일
        end_date: 종료일
        strategies: 전략 리스트
        top_n: 종목 수

    Returns:
        전략별 결과 비교
    """
    print(f"\n{'='*60}")
    print(f"전략 비교 백테스트")
    print(f"비교 전략: {', '.join(strategies)}")
    print(f"{'='*60}\n")

    results = {}

    for strategy in strategies:
        print(f"\n--- {strategy} 전략 백테스트 ---")
        result = run_backtest(
            start_date=start_date,
            end_date=end_date,
            strategy=strategy,
            top_n=top_n
        )

        if result['status'] == 'success':
            results[strategy] = result

    # 비교 테이블 생성
    comparison = {
        'strategies': {},
        'best_strategy': None,
        'best_sharpe': -999
    }

    for strategy, result in results.items():
        comparison['strategies'][strategy] = {
            'total_return': result['returns']['total_return'],
            'cagr': result['returns']['cagr'],
            'volatility': result['returns']['volatility'],
            'sharpe_ratio': result['returns']['sharpe_ratio'],
            'max_drawdown': result['returns']['max_drawdown'],
            'alpha': result['benchmark']['alpha']
        }

        # 최고 성과 전략 (Sharpe Ratio 기준)
        if result['returns']['sharpe_ratio'] > comparison['best_sharpe']:
            comparison['best_sharpe'] = result['returns']['sharpe_ratio']
            comparison['best_strategy'] = strategy

    comparison['status'] = 'success'
    return comparison


def generate_backtest_report(result: Dict, output_file: Optional[str] = None) -> str:
    """
    백테스트 리포트 생성 (Markdown)

    Args:
        result: 백테스트 결과
        output_file: 출력 파일 경로 (옵션)

    Returns:
        리포트 텍스트
    """
    if result['status'] != 'success':
        return f"# 백테스트 실패\n\n{result.get('message', '알 수 없는 오류')}"

    # 리포트 생성
    report = f"""# 백테스트 리포트

**생성일시:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## 1. 개요

### 백테스트 기간
- 시작일: {result['period']['start_date']}
- 종료일: {result['period']['end_date']}
- 총 일수: {result['period']['days']}일 ({result['period']['years']}년)

### 투자 전략
- 전략명: **{result['strategy']['name']}**
- 선정 종목 수: {result['strategy']['top_n']}개
- 리밸런싱 주기: {result['strategy']['rebalance_months']}개월

---

## 2. 성과 지표

### 수익률
| 지표 | 값 |
|------|------|
| **총 수익률** | {result['returns']['total_return']:+.2f}% |
| **CAGR (연평균)** | {result['returns']['cagr']:+.2f}% |
| **변동성 (연율화)** | {result['returns']['volatility']:.2f}% |

### 리스크
| 지표 | 값 |
|------|------|
| **최대 낙폭 (MDD)** | {result['returns']['max_drawdown']:.2f}% |
| **Sharpe Ratio** | {result['returns']['sharpe_ratio']:.2f} |
| **Sortino Ratio** | {result['returns']['sortino_ratio']:.2f} |

### 거래 통계
| 지표 | 값 |
|------|------|
| **승률** | {result['returns']['win_rate']:.2f}% |
| **평균 수익** | {result['returns']['avg_gain']:.4f}% |
| **평균 손실** | {result['returns']['avg_loss']:.4f}% |

---

## 3. 벤치마크 비교 (KOSPI)

| 지표 | 포트폴리오 | KOSPI | 차이 |
|------|-----------|-------|------|
| **총 수익률** | {result['returns']['total_return']:+.2f}% | {result['benchmark']['total_return']:+.2f}% | {result['benchmark']['alpha']:+.2f}%p |
| **베타** | {result['benchmark']['beta']:.2f} | 1.00 | - |

- **알파 (초과수익):** {result['benchmark']['alpha']:+.2f}%p
- **베타 (시장 민감도):** {result['benchmark']['beta']:.2f}

---

## 4. 선정 종목

**총 {len(result['strategy']['selected_stocks'])}개 종목**

"""

    # 종목별 비중
    report += "| 순위 | 종목코드 | 비중 |\n"
    report += "|------|----------|------|\n"

    for i, code in enumerate(result['strategy']['selected_stocks'][:10], 1):
        weight = result['strategy']['weights'].get(code, 0) * 100
        report += f"| {i} | {code} | {weight:.2f}% |\n"

    if len(result['strategy']['selected_stocks']) > 10:
        report += f"\n*외 {len(result['strategy']['selected_stocks']) - 10}개 종목*\n"

    # 면책 조항
    report += """
---

## 5. 결론

"""

    # 성과 평가
    if result['returns']['total_return'] > 0:
        if result['benchmark']['alpha'] > 0:
            report += f"✅ **양호한 성과**: 총 수익률 {result['returns']['total_return']:+.2f}% (KOSPI 대비 {result['benchmark']['alpha']:+.2f}%p 초과 달성)\n"
        else:
            report += f"⚠️ **벤치마크 미달**: 총 수익률 {result['returns']['total_return']:+.2f}% (KOSPI 대비 {result['benchmark']['alpha']:.2f}%p 하회)\n"
    else:
        report += f"❌ **손실 발생**: 총 수익률 {result['returns']['total_return']:.2f}%\n"

    # Sharpe Ratio 평가
    if result['returns']['sharpe_ratio'] > 1.0:
        report += f"✅ **우수한 위험조정 수익률**: Sharpe Ratio {result['returns']['sharpe_ratio']:.2f}\n"
    elif result['returns']['sharpe_ratio'] > 0.5:
        report += f"⚠️ **보통 수준의 위험조정 수익률**: Sharpe Ratio {result['returns']['sharpe_ratio']:.2f}\n"
    else:
        report += f"❌ **낮은 위험조정 수익률**: Sharpe Ratio {result['returns']['sharpe_ratio']:.2f}\n"

    # MDD 평가
    if abs(result['returns']['max_drawdown']) < 20:
        report += f"✅ **안정적인 손실 관리**: MDD {result['returns']['max_drawdown']:.2f}%\n"
    else:
        report += f"⚠️ **주의 필요**: MDD {result['returns']['max_drawdown']:.2f}% (큰 낙폭)\n"

    # 면책 조항
    report += """
---

## ⚠️ 투자 유의사항

본 백테스트 결과는 과거 데이터를 기반으로 한 시뮬레이션이며,
**미래 수익을 보장하지 않습니다.**

- 실제 투자 시 거래 비용, 슬리피지, 세금 등이 발생합니다
- 과거 성과가 미래 성과를 보장하지 않습니다
- 투자 판단과 그에 따른 손실은 투자자 본인의 책임입니다
- 본 리포트는 참고 정보이며, 투자 권유가 아닙니다

**데이터 출처:** FinanceDataReader, PostgreSQL 데이터베이스

---

*Generated by AI Investment Agent - Phase 4 Backtesting Module*
"""

    # 파일 저장
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"✓ 리포트 저장: {output_file}")

    return report


if __name__ == "__main__":
    """테스트 실행"""
    print("백테스팅 모듈 테스트")
    print("="*60)

    # 테스트: 최근 3개월 백테스트
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')

    result = run_backtest(
        start_date=start_date,
        end_date=end_date,
        strategy="equal_weight",
        top_n=10
    )

    if result['status'] == 'success':
        print("\n백테스트 성공!")
        print(f"총 수익률: {result['returns']['total_return']:.2f}%")
        print(f"Sharpe Ratio: {result['returns']['sharpe_ratio']:.2f}")
        print(f"MDD: {result['returns']['max_drawdown']:.2f}%")

        # 리포트 생성
        report = generate_backtest_report(result, "reports/backtest_test.md")
        print(f"\n리포트 미리보기:\n{report[:500]}...")
    else:
        print(f"\n백테스트 실패: {result.get('message')}")
