"""
대시보드 데이터 조회 모듈

대시보드에서 필요한 데이터를 조회하는 함수들
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import pandas as pd
import json

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from core.utils.db_utils import get_db_connection

# 같은 디렉토리의 모듈들 import
sys.path.insert(0, str(Path(__file__).parent))

import portfolio_manager as pm
import ai_analysis_storage as ai_storage


def get_account_summary(account_id: int = 1) -> Dict:
    """
    계좌 요약 정보 조회

    Args:
        account_id: 계좌 ID

    Returns:
        Dict: {
            'account_id': int,
            'account_name': str,
            'initial_balance': float,
            'cash_balance': float,
            'stock_value': float,
            'total_value': float,
            'total_return': float,
            'return_pct': float,
            'num_positions': int
        }
    """
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT
                account_id,
                account_name,
                initial_balance,
                cash_balance,
                COALESCE(stock_value, 0) as stock_value,
                COALESCE(total_value, 0) as total_value,
                COALESCE(return_pct, 0) as return_pct,
                COALESCE(num_positions, 0) as num_positions
            FROM v_account_summary
            WHERE account_id = %s
        """, (account_id,))

        row = cur.fetchone()

        if not row:
            return {
                'account_id': account_id,
                'account_name': 'Unknown',
                'initial_balance': 0,
                'cash_balance': 0,
                'stock_value': 0,
                'total_value': 0,
                'total_return': 0,
                'return_pct': 0,
                'num_positions': 0
            }

        # total_return 계산
        total_return = float(row[5]) - float(row[2])  # total_value - initial_balance

        return {
            'account_id': row[0],
            'account_name': row[1],
            'initial_balance': float(row[2]),
            'cash_balance': float(row[3]),
            'stock_value': float(row[4]),
            'total_value': float(row[5]),
            'total_return': total_return,
            'return_pct': float(row[6]),
            'num_positions': int(row[7])
        }

    finally:
        cur.close()
        conn.close()


def get_portfolio_positions(account_id: int = 1) -> pd.DataFrame:
    """
    포트폴리오 포지션 조회

    Args:
        account_id: 계좌 ID

    Returns:
        DataFrame: 포지션 정보 (code, name, sector, quantity, avg_price, current_price,
                              current_value, profit_loss, profit_loss_pct, weight_pct)
    """
    conn = get_db_connection()

    try:
        query = """
            SELECT
                code,
                stock_name as name,
                sector,
                quantity,
                avg_price,
                current_price,
                current_value,
                profit_loss,
                profit_loss_pct,
                weight_pct,
                first_buy_date
            FROM v_position_details
            WHERE account_id = %s
            ORDER BY current_value DESC
        """

        df = pd.read_sql_query(query, conn, params=(account_id,))

        if len(df) > 0:
            # 숫자 컬럼 정규화
            for col in ["quantity", "avg_price", "current_price", "current_value", "profit_loss", "profit_loss_pct"]:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')

            quantity = df.get("quantity")
            avg_price = df.get("avg_price")
            current_price = df.get("current_price")

            if "profit_loss" not in df.columns:
                df["profit_loss"] = (current_price - avg_price) * quantity
            else:
                missing_profit_mask = df["profit_loss"].isna()
                if missing_profit_mask.any():
                    df.loc[missing_profit_mask, "profit_loss"] = (
                        (current_price - avg_price) * quantity
                    )

            if "profit_loss_pct" not in df.columns:
                base = avg_price.replace(0, pd.NA)
                df["profit_loss_pct"] = ((df["profit_loss"] / base) * 100).fillna(0.0)
            else:
                missing_profit_pct_mask = df["profit_loss_pct"].isna()
                if missing_profit_pct_mask.any():
                    base = avg_price.replace(0, pd.NA)
                    df.loc[missing_profit_pct_mask, "profit_loss_pct"] = (
                        (df.loc[missing_profit_pct_mask, "profit_loss"] / base.loc[missing_profit_pct_mask]) * 100
                    ).fillna(0.0)
                df["profit_loss_pct"] = df["profit_loss_pct"].fillna(0.0)

        return df

    finally:
        conn.close()


def get_performance_metrics(account_id: int = 1) -> Dict:
    """
    성과 지표 조회

    Args:
        account_id: 계좌 ID

    Returns:
        Dict: {
            'total_trades': int,
            'buy_trades': int,
            'sell_trades': int,
            'winning_trades': int,
            'win_rate': float,
            'avg_profit_per_trade': float,
            'realized_profit': float,
            'unrealized_profit': float,
            'sharpe_ratio': float,
            'max_drawdown': float,
            'volatility': float
        }
    """
    # 기본 거래 통계
    metrics = pm.calculate_portfolio_metrics(account_id)

    # 히스토리에서 추가 지표 계산
    try:
        history_df = get_portfolio_history(account_id, days=30)

        if len(history_df) > 1:
            # Sharpe Ratio 계산 (총 자산 기준 일간 수익률)
            returns = history_df['total_value'].pct_change().dropna()
            if len(returns) > 0:
                sharpe_ratio = (returns.mean() / returns.std()) * (252 ** 0.5) if returns.std() > 0 else 0
            else:
                sharpe_ratio = 0

            # Maximum Drawdown 계산
            cummax = history_df['total_value'].cummax()
            drawdown = (history_df['total_value'] - cummax) / cummax * 100
            max_drawdown = drawdown.min()

            # 변동성 계산
            volatility = returns.std() * (252 ** 0.5) * 100 if len(returns) > 0 else 0

        else:
            sharpe_ratio = 0
            max_drawdown = 0
            volatility = 0

    except Exception as e:
        print(f"추가 지표 계산 실패: {e}")
        sharpe_ratio = 0
        max_drawdown = 0
        volatility = 0

    return {
        'total_trades': metrics.get('num_trades', 0),
        'buy_trades': metrics.get('buy_count', 0),
        'sell_trades': metrics.get('sell_count', 0),
        'winning_trades': metrics.get('winning_trades', 0),
        'win_rate': metrics.get('win_rate', 0),
        'avg_profit_per_trade': metrics.get('avg_profit_per_trade', 0),
        'realized_profit': metrics.get('realized_profit', 0),
        'unrealized_profit': metrics.get('unrealized_profit', 0),
        'sharpe_ratio': sharpe_ratio,
        'max_drawdown': max_drawdown,
        'volatility': volatility
    }


def get_portfolio_history(account_id: int = 1, days: int = 30) -> pd.DataFrame:
    """
    포트폴리오 히스토리 조회

    Args:
        account_id: 계좌 ID
        days: 조회 일수

    Returns:
        DataFrame: 히스토리 (snapshot_date, total_value, cash_balance, stock_value, return_pct)
    """
    conn = get_db_connection()

    try:
        query = """
            SELECT
                snapshot_date,
                total_value,
                cash_balance,
                stock_value,
                return_pct
            FROM virtual_portfolio_history
            WHERE account_id = %s
              AND snapshot_date >= CURRENT_DATE - %s::interval
            ORDER BY snapshot_date ASC
        """

        interval = f"{days} days"
        df = pd.read_sql_query(query, conn, params=(account_id, interval))

        # 날짜 컬럼을 datetime으로 변환
        if len(df) > 0 and 'snapshot_date' in df.columns:
            df['snapshot_date'] = pd.to_datetime(df['snapshot_date'])

        return df

    finally:
        conn.close()


def get_recent_trades(account_id: int = 1, limit: int = 50,
                      trade_type: Optional[str] = None,
                      start_date: Optional[str] = None,
                      end_date: Optional[str] = None) -> pd.DataFrame:
    """
    최근 거래 내역 조회

    Args:
        account_id: 계좌 ID
        limit: 조회 건수
        trade_type: 거래 유형 필터 ('buy' 또는 'sell')
        start_date: 시작 날짜 (YYYY-MM-DD)
        end_date: 종료 날짜 (YYYY-MM-DD)

    Returns:
        DataFrame: 거래 내역 (trade_id, trade_date, code, name, trade_type, quantity,
                            price, total_amount, commission, reason)
    """
    conn = get_db_connection()

    try:
        where_conditions = ["account_id = %s"]
        params = [account_id]

        if trade_type:
            where_conditions.append("trade_type = %s")
            params.append(trade_type)

        if start_date:
            where_conditions.append("trade_date >= %s")
            params.append(start_date)

        if end_date:
            where_conditions.append("trade_date <= %s")
            params.append(end_date)

        where_clause = " AND ".join(where_conditions)

        query = f"""
            SELECT
                trade_id,
                trade_date,
                code,
                stock_name as name,
                trade_type,
                quantity,
                price,
                total_amount,
                commission,
                reason
            FROM v_trade_details
            WHERE {where_clause}
            ORDER BY trade_date DESC, trade_id DESC
            LIMIT %s
        """

        params.append(limit)

        df = pd.read_sql_query(query, conn, params=tuple(params))

        # 날짜 컬럼을 datetime으로 변환
        if len(df) > 0 and 'trade_date' in df.columns:
            df['trade_date'] = pd.to_datetime(df['trade_date'])

        return df

    finally:
        conn.close()


def get_daily_returns(account_id: int = 1, days: int = 30) -> pd.DataFrame:
    """
    일별 수익률 조회

    Args:
        account_id: 계좌 ID
        days: 조회 일수

    Returns:
        DataFrame: 일별 수익률 (date, daily_return)
    """
    history_df = get_portfolio_history(account_id, days)

    if len(history_df) < 2:
        return pd.DataFrame(columns=['date', 'daily_return'])

    # 일별 수익률 계산
    history_df['daily_return'] = history_df['total_value'].pct_change() * 100

    result_df = history_df[['snapshot_date', 'daily_return']].copy()
    result_df.columns = ['date', 'daily_return']

    # NaN 제거
    result_df = result_df.dropna()

    return result_df


def get_daily_performance_stats(account_id: int = 1, days: int = 90) -> Dict:
    """
    최근 n일 간 일별 수익률 통계

    Returns:
        Dict: {
            'best_date': str,
            'best_return': float,
            'worst_date': str,
            'worst_return': float,
            'average_return': float
        }
    """
    history_df = get_portfolio_history(account_id, days)

    if len(history_df) < 2:
        return {
            'best_date': None,
            'best_return': 0.0,
            'worst_date': None,
            'worst_return': 0.0,
            'average_return': 0.0
        }

    history_df = history_df.sort_values('snapshot_date')
    history_df['daily_return'] = history_df['total_value'].pct_change() * 100
    history_df = history_df.dropna(subset=['daily_return'])

    if history_df.empty:
        return {
            'best_date': None,
            'best_return': 0.0,
            'worst_date': None,
            'worst_return': 0.0,
            'average_return': 0.0
        }

    best_row = history_df.loc[history_df['daily_return'].idxmax()]
    worst_row = history_df.loc[history_df['daily_return'].idxmin()]

    return {
        'best_date': best_row['snapshot_date'].strftime('%Y-%m-%d'),
        'best_return': float(best_row['daily_return']),
        'worst_date': worst_row['snapshot_date'].strftime('%Y-%m-%d'),
        'worst_return': float(worst_row['daily_return']),
        'average_return': float(history_df['daily_return'].mean())
    }


def get_monthly_returns(account_id: int = 1, months: int = 6) -> pd.DataFrame:
    """
    최근 n개월 월간 수익률 조회

    Returns:
        DataFrame: (period, return_pct)
    """
    days = max(months * 31, 60)
    history_df = get_portfolio_history(account_id, days=days)

    if len(history_df) < 2:
        return pd.DataFrame(columns=['period', 'return_pct'])

    history_df = history_df.sort_values('snapshot_date').set_index('snapshot_date')
    monthly_values = history_df['total_value'].resample('M').last()
    monthly_returns = monthly_values.pct_change() * 100
    monthly_returns = monthly_returns.dropna().tail(months)

    if len(monthly_returns) == 0:
        return pd.DataFrame(columns=['period', 'return_pct'])

    result = monthly_returns.reset_index()
    result.columns = ['snapshot_date', 'return_pct']
    result['period'] = result['snapshot_date'].dt.strftime('%Y-%m')

    return result[['period', 'return_pct']]


def get_benchmark_history(code: str = "KS11", days: int = 30) -> pd.DataFrame:
    """벤치마크 지수 일별 종가"""
    conn = get_db_connection()

    try:
        query = """
            SELECT date, close
            FROM prices
            WHERE code = %s
              AND date >= CURRENT_DATE - %s::interval
            ORDER BY date ASC
        """
        interval = f"{days} days"
        df = pd.read_sql_query(query, conn, params=(code, interval))

        if len(df) > 0:
            df['date'] = pd.to_datetime(df['date'])

        return df

    finally:
        conn.close()


def get_benchmark_monthly_returns(code: str = "KS11", months: int = 6) -> pd.DataFrame:
    """벤치마크 월간 수익률"""
    days = max(months * 31, 60)
    history = get_benchmark_history(code, days)

    if len(history) < 2:
        return pd.DataFrame(columns=['period', 'return_pct'])

    history = history.sort_values('date').set_index('date')
    monthly_close = history['close'].resample('M').last()
    monthly_returns = monthly_close.pct_change() * 100
    monthly_returns = monthly_returns.dropna().tail(months)

    if len(monthly_returns) == 0:
        return pd.DataFrame(columns=['period', 'return_pct'])

    result = monthly_returns.reset_index()
    result.columns = ['date', 'return_pct']
    result['period'] = result['date'].dt.strftime('%Y-%m')

    return result[['period', 'return_pct']]


def get_last_update_time(account_id: int = 1) -> Optional[datetime]:
    """
    마지막 업데이트 시간 조회

    Args:
        account_id: 계좌 ID

    Returns:
        datetime: 마지막 업데이트 시간
    """
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # 포트폴리오의 마지막 업데이트 시간 조회
        cur.execute("""
            SELECT MAX(updated_at)
            FROM virtual_portfolio
            WHERE account_id = %s
        """, (account_id,))

        result = cur.fetchone()

        if result and result[0]:
            return result[0]

        return None

    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    # 테스트 코드
    print("=== 계좌 요약 ===")
    summary = get_account_summary()
    for key, value in summary.items():
        print(f"{key}: {value}")

    print("\n=== 포트폴리오 포지션 ===")
    positions = get_portfolio_positions()
    print(positions)

    print("\n=== 성과 지표 ===")
    metrics = get_performance_metrics()
    for key, value in metrics.items():
        print(f"{key}: {value}")

    print("\n=== 최근 거래 내역 ===")
    trades = get_recent_trades(limit=10)
    print(trades)


# ===== AI 분석 데이터 조회 함수 =====

def get_holding_ai_analysis(account_id: int = 1) -> List[Dict]:
    """
    보유 종목의 AI 분석 정보 조회

    Args:
        account_id: 계좌 ID

    Returns:
        List[Dict]: 각 보유 종목의 AI 분석 정보
            - code: 종목 코드
            - name: 종목명
            - quantity: 보유 수량
            - profit_loss_pct: 손익률
            - overall_score: AI 종합 점수
            - target_price: 목표가
            - confidence_level: 신뢰도
            - risk_grade: 리스크 등급
            - buy_rationale: 매수 근거
            - analysis_date: 분석 날짜
    """
    try:
        holding_analysis = ai_storage.get_holding_analysis(account_id)
        return holding_analysis
    except Exception as e:
        print(f"AI 분석 조회 실패: {e}")
        return []


def get_portfolio_ai_summary(account_id: int = 1) -> Optional[Dict]:
    """
    포트폴리오의 최신 AI 인사이트 조회

    Args:
        account_id: 계좌 ID

    Returns:
        Dict: AI 포트폴리오 인사이트
            - expected_return: 기대 수익률
            - expected_volatility: 기대 변동성
            - sharpe_ratio: 샤프 비율
            - market_sentiment: 시장 전망
            - sector_allocation: 섹터 배분
            - portfolio_analysis: 포트폴리오 분석
            - recommendations: 추천사항
    """
    try:
        summary = ai_storage.get_portfolio_ai_summary(account_id)
        return summary
    except Exception as e:
        print(f"포트폴리오 AI 인사이트 조회 실패: {e}")
        return None


def get_stock_detail_analysis(code: str) -> Optional[Dict]:
    """
    특정 종목의 상세 AI 분석 정보 조회

    Args:
        code: 종목 코드

    Returns:
        Dict: 상세 AI 분석 정보 (최신 분석)
    """
    try:
        analyses = ai_storage.get_stock_analysis(code, limit=1)
        if analyses:
            return analyses[0]
        return None
    except Exception as e:
        print(f"종목 상세 분석 조회 실패 ({code}): {e}")
        return None


def get_high_score_recommendations(min_score: float = 70, limit: int = 10) -> List[Dict]:
    """
    높은 점수의 추천 종목 조회

    Args:
        min_score: 최소 점수 기준
        limit: 조회 개수

    Returns:
        List[Dict]: 높은 점수 종목 리스트
            - code: 종목 코드
            - overall_score: 종합 점수
            - target_price: 목표가
            - confidence_level: 신뢰도
            - risk_grade: 리스크 등급
            - buy_rationale: 매수 근거
    """
    try:
        return ai_storage.AIAnalysisStorage.get_high_score_stocks(
            min_score=min_score,
            limit=limit
        )
    except Exception as e:
        print(f"높은 점수 종목 조회 실패: {e}")
        return []


def get_sector_allocation_analysis(account_id: int = 1) -> Dict[str, Dict]:
    """
    포트폴리오의 섹터별 배분 및 AI 점수 분석

    Args:
        account_id: 계좌 ID

    Returns:
        Dict: 섹터별 정보
            - weight: 섹터 비중
            - avg_score: 평균 AI 점수
            - num_holdings: 보유 종목 수
            - avg_risk_grade: 평균 리스크 등급
    """
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT
                s.sector,
                COUNT(p.position_id) as num_holdings,
                SUM(p.current_value) as total_value,
                AVG(CAST(a.overall_score AS FLOAT)) as avg_score
            FROM virtual_portfolio p
            JOIN stocks s ON p.code = s.code
            LEFT JOIN LATERAL (
                SELECT overall_score
                FROM ai_stock_analysis
                WHERE code = p.code
                ORDER BY analysis_date DESC
                LIMIT 1
            ) a ON TRUE
            WHERE p.account_id = %s AND p.quantity > 0
            GROUP BY s.sector
            ORDER BY total_value DESC
        """, (account_id,))

        # 전체 포트폴리오 가치 조회
        cur.execute("""
            SELECT
                current_balance + COALESCE(SUM(current_value), 0) as total_portfolio_value
            FROM virtual_accounts a
            LEFT JOIN virtual_portfolio p ON a.account_id = p.account_id AND p.quantity > 0
            WHERE a.account_id = %s
            GROUP BY a.account_id, a.current_balance
        """, (account_id,))

        portfolio_result = cur.fetchone()
        total_portfolio_value = float(portfolio_result[0]) if portfolio_result else 1

        # 섹터별 데이터 구성
        sector_data = {}
        for row in cur.description:
            pass  # Reset after fetching

        cur.execute("""
            SELECT
                s.sector,
                COUNT(p.position_id) as num_holdings,
                SUM(p.current_value) as total_value,
                AVG(CAST(a.overall_score AS FLOAT)) as avg_score
            FROM virtual_portfolio p
            JOIN stocks s ON p.code = s.code
            LEFT JOIN LATERAL (
                SELECT overall_score
                FROM ai_stock_analysis
                WHERE code = p.code
                ORDER BY analysis_date DESC
                LIMIT 1
            ) a ON TRUE
            WHERE p.account_id = %s AND p.quantity > 0
            GROUP BY s.sector
            ORDER BY total_value DESC
        """, (account_id,))

        for row in cur.fetchall():
            sector, num_holdings, total_value, avg_score = row
            sector_data[sector] = {
                'weight': float(total_value or 0) / total_portfolio_value * 100,
                'num_holdings': int(num_holdings),
                'avg_score': float(avg_score) if avg_score else 0,
                'total_value': float(total_value or 0)
            }

        return sector_data

    except Exception as e:
        print(f"섹터 배분 분석 실패: {e}")
        return {}

    finally:
        cur.close()
        conn.close()
