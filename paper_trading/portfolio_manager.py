"""
포트폴리오 관리 모듈

포트폴리오 리밸런싱, 리스크 관리, 일일 스냅샷 등
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, date
from collections import defaultdict

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from core.utils.db_utils import get_db_connection

# 같은 디렉토리의 paper_trading 모듈 import를 위해 현재 디렉토리 추가
sys.path.insert(0, str(Path(__file__).parent))

# paper_trading 패키지에서 함수 import
import paper_trading as pt
get_portfolio = pt.get_portfolio
update_portfolio_values = pt.update_portfolio_values
execute_buy = pt.execute_buy
execute_sell = pt.execute_sell
get_latest_price = pt.get_latest_price


def save_daily_snapshot(account_id: int) -> Dict:
    """
    일일 포트폴리오 스냅샷 저장

    Args:
        account_id: 계좌 ID

    Returns:
        Dict: 스냅샷 정보
    """
    # 먼저 포트폴리오 값 업데이트
    update_portfolio_values(account_id)

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # 계좌 요약 정보 조회
        cur.execute("""
            SELECT
                initial_balance,
                cash_balance,
                stock_value,
                total_value,
                return_pct
            FROM v_account_summary
            WHERE account_id = %s
        """, (account_id,))

        row = cur.fetchone()
        if not row:
            raise ValueError(f"계좌 ID {account_id}를 찾을 수 없습니다")

        initial_balance, cash_balance, stock_value, total_value, return_pct = row

        # 스냅샷 저장
        cur.execute("""
            INSERT INTO virtual_portfolio_history (
                account_id, snapshot_date, total_value, cash_balance, stock_value, return_pct
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (account_id, snapshot_date)
            DO UPDATE SET
                total_value = EXCLUDED.total_value,
                cash_balance = EXCLUDED.cash_balance,
                stock_value = EXCLUDED.stock_value,
                return_pct = EXCLUDED.return_pct,
                created_at = CURRENT_TIMESTAMP
        """, (account_id, date.today(), total_value, cash_balance, stock_value, return_pct))

        conn.commit()

        return {
            'snapshot_date': date.today().isoformat(),
            'total_value': float(total_value),
            'cash_balance': float(cash_balance),
            'stock_value': float(stock_value),
            'return_pct': float(return_pct) if return_pct else 0.0
        }

    finally:
        cur.close()
        conn.close()


def get_portfolio_history(account_id: int, days: int = 30) -> List[Dict]:
    """
    포트폴리오 히스토리 조회

    Args:
        account_id: 계좌 ID
        days: 조회할 일수 (기본값: 30일)

    Returns:
        List[Dict]: 히스토리 리스트
    """
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT
                snapshot_date,
                total_value,
                cash_balance,
                stock_value,
                return_pct
            FROM virtual_portfolio_history
            WHERE account_id = %s
            ORDER BY snapshot_date DESC
            LIMIT %s
        """, (account_id, days))

        history = []
        for row in cur.fetchall():
            history.append({
                'date': row[0].isoformat(),
                'total_value': float(row[1]),
                'cash_balance': float(row[2]),
                'stock_value': float(row[3]),
                'return_pct': float(row[4]) if row[4] else 0.0
            })

        return history

    finally:
        cur.close()
        conn.close()


def check_stop_loss_take_profit(account_id: int,
                                 stop_loss_pct: float = -10.0,
                                 take_profit_pct: float = 20.0) -> List[Dict]:
    """
    손절/익절 체크 및 매도 권장 종목 리스트 반환

    Args:
        account_id: 계좌 ID
        stop_loss_pct: 손절 기준 (%, 기본값: -10%)
        take_profit_pct: 익절 기준 (%, 기본값: +20%)

    Returns:
        List[Dict]: 매도 권장 종목 리스트
            - code: 종목 코드
            - name: 종목명
            - quantity: 보유 수량
            - profit_loss_pct: 수익률
            - reason: 매도 사유 ('stop_loss' 또는 'take_profit')
    """
    portfolio = get_portfolio(account_id)
    recommendations = []

    for position in portfolio['positions']:
        profit_loss_pct = position['profit_loss_pct']

        if profit_loss_pct <= stop_loss_pct:
            recommendations.append({
                'code': position['code'],
                'name': position['name'],
                'quantity': position['quantity'],
                'profit_loss_pct': profit_loss_pct,
                'reason': 'stop_loss',
                'message': f"손절 기준 도달 ({profit_loss_pct:.2f}% ≤ {stop_loss_pct}%)"
            })

        elif profit_loss_pct >= take_profit_pct:
            recommendations.append({
                'code': position['code'],
                'name': position['name'],
                'quantity': position['quantity'],
                'profit_loss_pct': profit_loss_pct,
                'reason': 'take_profit',
                'message': f"익절 기준 도달 ({profit_loss_pct:.2f}% ≥ {take_profit_pct}%)"
            })

    return recommendations


def execute_rebalancing(account_id: int, target_weights: Dict[str, float],
                       max_trade_pct: float = 0.05) -> Dict:
    """
    포트폴리오 리밸런싱 실행

    Args:
        account_id: 계좌 ID
        target_weights: 목표 비중 딕셔너리 {종목코드: 비중(0-1)}
        max_trade_pct: 리밸런싱 실행 기준 (비중 차이 %, 기본값: 5%p)

    Returns:
        Dict: 리밸런싱 결과
            - executed_trades: 실행된 거래 리스트
            - total_trades: 총 거래 수
            - total_amount: 총 거래 금액
    """
    # 현재 포트폴리오 조회
    portfolio = get_portfolio(account_id)
    total_value = portfolio['total_value']

    executed_trades = []
    total_amount = 0

    # 현재 비중 계산
    current_weights = {}
    for position in portfolio['positions']:
        current_weights[position['code']] = position['current_value'] / total_value

    # 각 종목별로 리밸런싱 필요 여부 확인
    for code, target_weight in target_weights.items():
        current_weight = current_weights.get(code, 0)
        weight_diff = target_weight - current_weight

        # 비중 차이가 max_trade_pct 이상이면 리밸런싱
        if abs(weight_diff) < max_trade_pct:
            continue

        # 목표 평가액 계산
        target_value = total_value * target_weight
        current_value = total_value * current_weight
        trade_value = target_value - current_value

        # 현재가 조회
        current_price = get_latest_price(code)
        if current_price is None:
            continue

        # 거래 수량 계산
        quantity = int(abs(trade_value) / current_price)
        if quantity == 0:
            continue

        try:
            if trade_value > 0:
                # 매수
                result = execute_buy(
                    account_id, code, quantity,
                    reason=f"리밸런싱: 비중 {current_weight*100:.1f}% → {target_weight*100:.1f}%"
                )
                executed_trades.append({
                    'action': 'buy',
                    'code': code,
                    'quantity': quantity,
                    'price': result['price'],
                    'amount': result['total_amount']
                })
                total_amount += result['total_amount']

            else:
                # 매도
                result = execute_sell(
                    account_id, code, quantity,
                    reason=f"리밸런싱: 비중 {current_weight*100:.1f}% → {target_weight*100:.1f}%"
                )
                executed_trades.append({
                    'action': 'sell',
                    'code': code,
                    'quantity': quantity,
                    'price': result['price'],
                    'amount': result['total_amount']
                })
                total_amount += result['total_amount']

        except Exception as e:
            print(f"⚠️  {code} 리밸런싱 실패: {e}")
            continue

    return {
        'executed_trades': executed_trades,
        'total_trades': len(executed_trades),
        'total_amount': total_amount
    }


def get_trade_history(account_id: int, limit: int = 50) -> List[Dict]:
    """
    거래 내역 조회

    Args:
        account_id: 계좌 ID
        limit: 조회할 개수 (기본값: 50)

    Returns:
        List[Dict]: 거래 내역 리스트
    """
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT
                trade_id,
                code,
                stock_name,
                trade_type,
                quantity,
                price,
                total_amount,
                commission,
                trade_date,
                reason
            FROM v_trade_details
            WHERE account_id = %s
            ORDER BY trade_date DESC
            LIMIT %s
        """, (account_id, limit))

        trades = []
        for row in cur.fetchall():
            trades.append({
                'trade_id': row[0],
                'code': row[1],
                'stock_name': row[2],
                'trade_type': row[3],
                'quantity': int(row[4]),
                'price': float(row[5]),
                'total_amount': float(row[6]),
                'commission': float(row[7]),
                'trade_date': row[8].isoformat(),
                'reason': row[9]
            })

        return trades

    finally:
        cur.close()
        conn.close()


def calculate_portfolio_metrics(account_id: int) -> Dict:
    """
    포트폴리오 성과 지표 계산

    Args:
        account_id: 계좌 ID

    Returns:
        Dict: 성과 지표
            - total_return: 총 수익
            - total_return_pct: 총 수익률
            - num_trades: 총 거래 수
            - win_rate: 승률 (%)
            - avg_profit_per_trade: 평균 거래당 수익
    """
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # 계좌 요약
        cur.execute("""
            SELECT initial_balance, total_value, return_pct
            FROM v_account_summary
            WHERE account_id = %s
        """, (account_id,))

        row = cur.fetchone()
        if not row:
            raise ValueError(f"계좌 ID {account_id}를 찾을 수 없습니다")

        initial_balance = float(row[0])
        total_value = float(row[1])
        return_pct = float(row[2]) if row[2] else 0.0

        total_return = total_value - initial_balance

        # 거래 통계 (거래 이력 재구성)
        cur.execute("""
            SELECT trade_id, trade_type, code, quantity, total_amount, commission, trade_date
            FROM virtual_trades
            WHERE account_id = %s
            ORDER BY trade_date ASC, trade_id ASC
        """, (account_id,))
        trade_rows = cur.fetchall()

        num_trades = len(trade_rows)
        buy_count = sum(1 for row in trade_rows if row[1] == 'buy')
        sell_count = sum(1 for row in trade_rows if row[1] == 'sell')

        # 포지션 원가 추적용 구조 (평균 단가 기반)
        position_costs: Dict[str, Dict[str, float]] = defaultdict(lambda: {'quantity': 0.0, 'total_cost': 0.0})
        winning_trades = 0

        realized_profit = 0.0

        for _, trade_type, code, quantity, total_amount, _commission, _ in trade_rows:
            qty = int(quantity)
            amount = float(total_amount)
            pos = position_costs[code]

            if trade_type == 'buy':
                pos['quantity'] += qty
                pos['total_cost'] += amount  # 수수료 포함 총 매입금액

            elif trade_type == 'sell':
                if pos['quantity'] <= 0:
                    # 예상치 못한 상태지만 계산은 계속 진행
                    cost_basis = 0.0
                else:
                    avg_cost = pos['total_cost'] / pos['quantity'] if pos['quantity'] else 0.0
                    cost_basis = avg_cost * qty

                profit = amount - cost_basis
                if profit > 0:
                    winning_trades += 1

                realized_profit += profit

                pos['quantity'] -= qty
                pos['total_cost'] -= cost_basis

                if pos['quantity'] <= 0:
                    pos['quantity'] = 0.0
                    pos['total_cost'] = 0.0

        win_rate = (winning_trades / sell_count * 100) if sell_count > 0 else 0.0
        avg_profit_per_trade = total_return / num_trades if num_trades > 0 else 0.0

        # 미실현 손익 (현재 보유 포지션 기준)
        cur.execute("""
            SELECT COALESCE(SUM(profit_loss), 0)
            FROM virtual_portfolio
            WHERE account_id = %s
        """, (account_id,))
        unrealized_profit = float(cur.fetchone()[0] or 0.0)

        return {
            'initial_balance': initial_balance,
            'total_value': total_value,
            'total_return': total_return,
            'total_return_pct': return_pct,
            'num_trades': num_trades,
            'buy_count': buy_count,
            'sell_count': sell_count,
            'winning_trades': winning_trades,
            'win_rate': win_rate,
            'avg_profit_per_trade': avg_profit_per_trade,
            'realized_profit': realized_profit,
            'unrealized_profit': unrealized_profit
        }

    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    """테스트 및 CLI"""
    import argparse

    parser = argparse.ArgumentParser(description="포트폴리오 관리")
    parser.add_argument("command", choices=["snapshot", "history", "check-exit", "metrics", "trades"],
                        help="실행할 명령")
    parser.add_argument("--account-id", type=int, default=1, help="계좌 ID")
    parser.add_argument("--days", type=int, default=30, help="조회 일수 (history)")
    parser.add_argument("--stop-loss", type=float, default=-10.0, help="손절 기준 % (check-exit)")
    parser.add_argument("--take-profit", type=float, default=20.0, help="익절 기준 % (check-exit)")
    parser.add_argument("--limit", type=int, default=50, help="조회 개수 (trades)")

    args = parser.parse_args()

    try:
        if args.command == "snapshot":
            result = save_daily_snapshot(args.account_id)
            print(f"✅ 일일 스냅샷 저장 완료")
            print(f"   날짜: {result['snapshot_date']}")
            print(f"   총 자산: {result['total_value']:,.0f}원")
            print(f"   수익률: {result['return_pct']:+.2f}%")

        elif args.command == "history":
            history = get_portfolio_history(args.account_id, args.days)
            print(f"\n📊 포트폴리오 히스토리 (최근 {len(history)}일)\n")
            print(f"{'날짜':<12} {'총자산':>15} {'현금':>15} {'주식':>15} {'수익률':>10}")
            print("-" * 75)
            for h in history:
                print(f"{h['date']:<12} {h['total_value']:>15,.0f} {h['cash_balance']:>15,.0f} "
                      f"{h['stock_value']:>15,.0f} {h['return_pct']:>9.2f}%")

        elif args.command == "check-exit":
            recommendations = check_stop_loss_take_profit(
                args.account_id, args.stop_loss, args.take_profit
            )
            if recommendations:
                print(f"\n⚠️  매도 권장 종목 ({len(recommendations)}개)\n")
                for rec in recommendations:
                    print(f"  • {rec['name']} ({rec['code']})")
                    print(f"    {rec['message']}")
                    print(f"    보유: {rec['quantity']:,}주\n")
            else:
                print("✅ 손절/익절 대상 종목 없음")

        elif args.command == "metrics":
            metrics = calculate_portfolio_metrics(args.account_id)
            print(f"\n📈 포트폴리오 성과 지표\n")
            print(f"초기 자금: {metrics['initial_balance']:>20,.0f}원")
            print(f"현재 자산: {metrics['total_value']:>20,.0f}원")
            print(f"총 수익: {metrics['total_return']:>22,.0f}원 ({metrics['total_return_pct']:+.2f}%)")
            print("-" * 50)
            print(f"총 거래 수: {metrics['num_trades']}회")
            print(f"매수 횟수: {metrics['buy_count']}회")
            print(f"매도 횟수: {metrics['sell_count']}회")
            print(f"승률: {metrics['win_rate']:.1f}% ({metrics['winning_trades']}/{metrics['sell_count']})")
            print(f"평균 거래당 수익: {metrics['avg_profit_per_trade']:,.0f}원")
            print(f"실현 손익: {metrics['realized_profit']:>18,.0f}원")
            print(f"미실현 손익: {metrics['unrealized_profit']:>16,.0f}원")

        elif args.command == "trades":
            trades = get_trade_history(args.account_id, args.limit)
            print(f"\n📋 거래 내역 (최근 {len(trades)}건)\n")
            print(f"{'날짜':<12} {'구분':<4} {'종목':<10} {'수량':>8} {'가격':>12} {'금액':>15} {'사유':<30}")
            print("-" * 110)
            for trade in trades:
                trade_type = "매수" if trade['trade_type'] == 'buy' else "매도"
                print(f"{trade['trade_date'][:10]:<12} {trade_type:<4} "
                      f"{trade['code']:<10} {trade['quantity']:>8,} "
                      f"{trade['price']:>12,.0f} {trade['total_amount']:>15,.0f} "
                      f"{trade['reason'][:30]:<30}")

    except Exception as e:
        print(f"❌ 오류: {e}")
        sys.exit(1)
