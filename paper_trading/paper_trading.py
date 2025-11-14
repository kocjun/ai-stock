"""
페이퍼 트레이딩 매매 실행 모듈

가상 계좌에서 매수/매도 주문 실행 및 포트폴리오 관리
"""

import sys
from pathlib import Path
from typing import Dict, Optional, Tuple
from decimal import Decimal
from datetime import datetime

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from core.utils.db_utils import get_db_connection


# 거래 수수료율 (0.015% - 한국 증권사 평균)
COMMISSION_RATE = 0.00015


class InsufficientFundsError(Exception):
    """잔고 부족 에러"""
    pass


class InsufficientSharesError(Exception):
    """보유 주식 부족 에러"""
    pass


class InvalidPriceError(Exception):
    """유효하지 않은 가격 에러"""
    pass


def get_latest_price(code: str) -> Optional[float]:
    """
    종목의 최신 종가 조회

    Args:
        code: 종목 코드

    Returns:
        float: 최신 종가 (없으면 None)
    """
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT close
            FROM prices
            WHERE code = %s
            ORDER BY date DESC
            LIMIT 1
        """, (code,))

        row = cur.fetchone()
        return float(row[0]) if row else None

    finally:
        cur.close()
        conn.close()


def get_current_balance(account_id: int) -> Decimal:
    """
    계좌의 현재 현금 잔고 조회

    Args:
        account_id: 계좌 ID

    Returns:
        Decimal: 현재 잔고
    """
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT current_balance
            FROM virtual_accounts
            WHERE account_id = %s
        """, (account_id,))

        row = cur.fetchone()
        if not row:
            raise ValueError(f"계좌 ID {account_id}를 찾을 수 없습니다")

        return row[0]

    finally:
        cur.close()
        conn.close()


def get_position(account_id: int, code: str) -> Optional[Dict]:
    """
    특정 종목의 보유 포지션 조회

    Args:
        account_id: 계좌 ID
        code: 종목 코드

    Returns:
        Dict: 포지션 정보 (없으면 None)
            - position_id: 포지션 ID
            - quantity: 보유 수량
            - avg_price: 평균 매입가
    """
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT position_id, quantity, avg_price
            FROM virtual_portfolio
            WHERE account_id = %s AND code = %s
        """, (account_id, code))

        row = cur.fetchone()
        if not row:
            return None

        return {
            'position_id': row[0],
            'quantity': int(row[1]),
            'avg_price': float(row[2])
        }

    finally:
        cur.close()
        conn.close()


def execute_buy(account_id: int, code: str, quantity: int,
                price: Optional[float] = None, reason: str = "") -> Dict:
    """
    매수 주문 실행

    Args:
        account_id: 계좌 ID
        code: 종목 코드
        quantity: 매수 수량
        price: 매수 가격 (None이면 최신 종가 사용)
        reason: 매수 사유

    Returns:
        Dict: 거래 정보
            - trade_id: 거래 ID
            - code: 종목 코드
            - quantity: 수량
            - price: 가격
            - total_amount: 총 금액 (수수료 포함)
            - commission: 수수료

    Raises:
        InsufficientFundsError: 잔고 부족
        InvalidPriceError: 유효하지 않은 가격
    """
    if quantity <= 0:
        raise ValueError(f"수량은 양수여야 합니다: {quantity}")

    # 가격 결정 (지정가 없으면 최신 종가)
    if price is None:
        price = get_latest_price(code)
        if price is None:
            raise InvalidPriceError(f"종목 {code}의 가격 정보를 찾을 수 없습니다")

    if price <= 0:
        raise InvalidPriceError(f"유효하지 않은 가격: {price}")

    # 매수 금액 계산 (수수료 포함)
    stock_amount = price * quantity
    commission = stock_amount * COMMISSION_RATE
    total_amount = stock_amount + commission

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # 잔고 확인
        current_balance = get_current_balance(account_id)
        if current_balance < total_amount:
            raise InsufficientFundsError(
                f"잔고 부족: 필요 금액 {total_amount:,.0f}원, 현재 잔고 {current_balance:,.0f}원"
            )

        # 1. 거래 기록
        cur.execute("""
            INSERT INTO virtual_trades (
                account_id, code, trade_type, quantity, price, total_amount, commission, reason
            )
            VALUES (%s, %s, 'buy', %s, %s, %s, %s, %s)
            RETURNING trade_id, trade_date
        """, (account_id, code, quantity, price, total_amount, commission, reason))

        trade_row = cur.fetchone()
        trade_id = trade_row[0]
        trade_date = trade_row[1]

        # 2. 잔고 차감
        new_balance = current_balance - Decimal(str(total_amount))
        cur.execute("""
            UPDATE virtual_accounts
            SET current_balance = %s
            WHERE account_id = %s
        """, (new_balance, account_id))

        # 3. 포지션 업데이트
        position = get_position(account_id, code)

        if position:
            # 기존 포지션이 있으면 평균가 계산
            old_quantity = position['quantity']
            old_avg_price = position['avg_price']

            new_quantity = old_quantity + quantity
            new_avg_price = (old_avg_price * old_quantity + price * quantity) / new_quantity

            cur.execute("""
                UPDATE virtual_portfolio
                SET quantity = %s,
                    avg_price = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE account_id = %s AND code = %s
            """, (new_quantity, new_avg_price, account_id, code))
        else:
            # 새 포지션 생성
            cur.execute("""
                INSERT INTO virtual_portfolio (
                    account_id, code, quantity, avg_price, first_buy_date
                )
                VALUES (%s, %s, %s, %s, %s)
            """, (account_id, code, quantity, price, trade_date))

        conn.commit()

        return {
            'trade_id': trade_id,
            'trade_date': trade_date,
            'code': code,
            'quantity': quantity,
            'price': price,
            'total_amount': total_amount,
            'commission': commission,
            'new_balance': float(new_balance)
        }

    except Exception as e:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


def execute_sell(account_id: int, code: str, quantity: int,
                 price: Optional[float] = None, reason: str = "") -> Dict:
    """
    매도 주문 실행

    Args:
        account_id: 계좌 ID
        code: 종목 코드
        quantity: 매도 수량
        price: 매도 가격 (None이면 최신 종가 사용)
        reason: 매도 사유

    Returns:
        Dict: 거래 정보
            - trade_id: 거래 ID
            - code: 종목 코드
            - quantity: 수량
            - price: 가격
            - total_amount: 총 금액 (수수료 차감 후)
            - commission: 수수료
            - profit_loss: 실현 손익

    Raises:
        InsufficientSharesError: 보유 수량 부족
        InvalidPriceError: 유효하지 않은 가격
    """
    if quantity <= 0:
        raise ValueError(f"수량은 양수여야 합니다: {quantity}")

    # 가격 결정
    if price is None:
        price = get_latest_price(code)
        if price is None:
            raise InvalidPriceError(f"종목 {code}의 가격 정보를 찾을 수 없습니다")

    if price <= 0:
        raise InvalidPriceError(f"유효하지 않은 가격: {price}")

    # 보유 수량 확인
    position = get_position(account_id, code)
    if not position:
        raise InsufficientSharesError(f"종목 {code}를 보유하고 있지 않습니다")

    if position['quantity'] < quantity:
        raise InsufficientSharesError(
            f"보유 수량 부족: 필요 {quantity}주, 보유 {position['quantity']}주"
        )

    # 매도 금액 계산 (수수료 차감)
    stock_amount = price * quantity
    commission = stock_amount * COMMISSION_RATE
    total_amount = stock_amount - commission

    # 실현 손익 계산
    avg_price = position['avg_price']
    profit_loss = (price - avg_price) * quantity

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # 1. 거래 기록
        cur.execute("""
            INSERT INTO virtual_trades (
                account_id, code, trade_type, quantity, price, total_amount, commission, reason
            )
            VALUES (%s, %s, 'sell', %s, %s, %s, %s, %s)
            RETURNING trade_id, trade_date
        """, (account_id, code, quantity, price, total_amount, commission, reason))

        trade_row = cur.fetchone()
        trade_id = trade_row[0]
        trade_date = trade_row[1]

        # 2. 잔고 증가
        current_balance = get_current_balance(account_id)
        new_balance = current_balance + Decimal(str(total_amount))

        cur.execute("""
            UPDATE virtual_accounts
            SET current_balance = %s
            WHERE account_id = %s
        """, (new_balance, account_id))

        # 3. 포지션 업데이트
        new_quantity = position['quantity'] - quantity

        if new_quantity > 0:
            # 일부 매도 - 수량만 감소
            cur.execute("""
                UPDATE virtual_portfolio
                SET quantity = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE account_id = %s AND code = %s
            """, (new_quantity, account_id, code))
        else:
            # 전량 매도 - 포지션 삭제
            cur.execute("""
                DELETE FROM virtual_portfolio
                WHERE account_id = %s AND code = %s
            """, (account_id, code))

        conn.commit()

        return {
            'trade_id': trade_id,
            'trade_date': trade_date,
            'code': code,
            'quantity': quantity,
            'price': price,
            'total_amount': total_amount,
            'commission': commission,
            'avg_price': avg_price,
            'profit_loss': profit_loss,
            'profit_loss_pct': (profit_loss / (avg_price * quantity)) * 100,
            'new_balance': float(new_balance),
            'remaining_quantity': new_quantity
        }

    except Exception as e:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


def update_portfolio_values(account_id: int) -> Dict:
    """
    포트폴리오 전체의 현재가 및 평가 손익 업데이트

    Args:
        account_id: 계좌 ID

    Returns:
        Dict: 업데이트 결과
            - updated_count: 업데이트된 포지션 수
            - total_value: 총 평가액
            - total_profit_loss: 총 평가 손익
    """
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # 모든 포지션 조회
        cur.execute("""
            SELECT code, quantity, avg_price
            FROM virtual_portfolio
            WHERE account_id = %s AND quantity > 0
        """, (account_id,))

        positions = cur.fetchall()

        updated_count = 0
        total_value = 0
        total_profit_loss = 0

        for code, quantity, avg_price in positions:
            # 최신 가격 조회
            current_price = get_latest_price(code)
            if current_price is None:
                continue

            # 평가액 및 손익 계산
            current_value = current_price * quantity
            cost = float(avg_price) * quantity
            profit_loss = current_value - cost
            profit_loss_pct = (profit_loss / cost) * 100 if cost > 0 else 0

            # 포지션 업데이트
            cur.execute("""
                UPDATE virtual_portfolio
                SET current_price = %s,
                    current_value = %s,
                    profit_loss = %s,
                    profit_loss_pct = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE account_id = %s AND code = %s
            """, (current_price, current_value, profit_loss, profit_loss_pct, account_id, code))

            updated_count += 1
            total_value += current_value
            total_profit_loss += profit_loss

        conn.commit()

        return {
            'updated_count': updated_count,
            'total_value': total_value,
            'total_profit_loss': total_profit_loss
        }

    finally:
        cur.close()
        conn.close()


def get_portfolio(account_id: int) -> Dict:
    """
    포트폴리오 전체 조회

    Args:
        account_id: 계좌 ID

    Returns:
        Dict: 포트폴리오 정보
            - cash_balance: 현금 잔고
            - positions: 보유 종목 리스트
            - total_stock_value: 주식 총 평가액
            - total_value: 총 자산
    """
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # 현금 잔고
        cash_balance = float(get_current_balance(account_id))

        # 보유 종목
        cur.execute("""
            SELECT
                p.code,
                s.name,
                p.quantity,
                p.avg_price,
                p.current_price,
                p.current_value,
                p.profit_loss,
                p.profit_loss_pct,
                p.first_buy_date
            FROM virtual_portfolio p
            JOIN stocks s ON p.code = s.code
            WHERE p.account_id = %s AND p.quantity > 0
            ORDER BY p.current_value DESC
        """, (account_id,))

        positions = []
        total_stock_value = 0

        for row in cur.fetchall():
            position = {
                'code': row[0],
                'name': row[1],
                'quantity': int(row[2]),
                'avg_price': float(row[3]),
                'current_price': float(row[4]) if row[4] else None,
                'current_value': float(row[5]) if row[5] else 0,
                'profit_loss': float(row[6]) if row[6] else 0,
                'profit_loss_pct': float(row[7]) if row[7] else 0,
                'first_buy_date': row[8].isoformat() if row[8] else None
            }
            positions.append(position)
            total_stock_value += position['current_value']

        total_value = cash_balance + total_stock_value

        return {
            'cash_balance': cash_balance,
            'positions': positions,
            'total_stock_value': total_stock_value,
            'total_value': total_value,
            'num_positions': len(positions)
        }

    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    """테스트 및 CLI"""
    import argparse

    parser = argparse.ArgumentParser(description="페이퍼 트레이딩 매매 실행")
    parser.add_argument("command", choices=["buy", "sell", "portfolio", "update"],
                        help="실행할 명령")
    parser.add_argument("--account-id", type=int, default=1, help="계좌 ID (기본값: 1)")
    parser.add_argument("--code", help="종목 코드 (buy, sell)")
    parser.add_argument("--quantity", type=int, help="수량 (buy, sell)")
    parser.add_argument("--price", type=float, help="가격 (지정하지 않으면 최신 종가)")
    parser.add_argument("--reason", default="", help="매매 사유")

    args = parser.parse_args()

    try:
        if args.command == "buy":
            if not args.code or not args.quantity:
                print("❌ --code와 --quantity를 지정해야 합니다")
                sys.exit(1)

            result = execute_buy(args.account_id, args.code, args.quantity, args.price, args.reason)
            print(f"✅ 매수 체결")
            print(f"   종목: {result['code']}")
            print(f"   수량: {result['quantity']:,}주")
            print(f"   가격: {result['price']:,.0f}원")
            print(f"   총 금액: {result['total_amount']:,.0f}원 (수수료 {result['commission']:,.0f}원 포함)")
            print(f"   남은 잔고: {result['new_balance']:,.0f}원")

        elif args.command == "sell":
            if not args.code or not args.quantity:
                print("❌ --code와 --quantity를 지정해야 합니다")
                sys.exit(1)

            result = execute_sell(args.account_id, args.code, args.quantity, args.price, args.reason)
            print(f"✅ 매도 체결")
            print(f"   종목: {result['code']}")
            print(f"   수량: {result['quantity']:,}주")
            print(f"   가격: {result['price']:,.0f}원")
            print(f"   총 금액: {result['total_amount']:,.0f}원 (수수료 {result['commission']:,.0f}원 차감)")
            print(f"   평균 매입가: {result['avg_price']:,.0f}원")
            print(f"   실현 손익: {result['profit_loss']:+,.0f}원 ({result['profit_loss_pct']:+.2f}%)")
            print(f"   남은 잔고: {result['new_balance']:,.0f}원")
            if result['remaining_quantity'] > 0:
                print(f"   남은 수량: {result['remaining_quantity']:,}주")

        elif args.command == "portfolio":
            portfolio = get_portfolio(args.account_id)
            print(f"\n💼 포트폴리오 (계좌 ID: {args.account_id})\n")
            print(f"현금 잔고: {portfolio['cash_balance']:>20,.0f}원")
            print(f"주식 평가액: {portfolio['total_stock_value']:>18,.0f}원")
            print(f"총 자산: {portfolio['total_value']:>22,.0f}원")
            print(f"\n보유 종목 ({portfolio['num_positions']}개):")
            print("-" * 100)
            print(f"{'종목코드':<8} {'종목명':<15} {'수량':>8} {'평균가':>12} {'현재가':>12} {'평가액':>15} {'손익':>12} {'수익률':>8}")
            print("-" * 100)

            for pos in portfolio['positions']:
                print(f"{pos['code']:<8} {pos['name']:<15} {pos['quantity']:>8,} "
                      f"{pos['avg_price']:>12,.0f} {pos['current_price']:>12,.0f} "
                      f"{pos['current_value']:>15,.0f} {pos['profit_loss']:>12,.0f} "
                      f"{pos['profit_loss_pct']:>7.2f}%")

        elif args.command == "update":
            result = update_portfolio_values(args.account_id)
            print(f"✅ 포트폴리오 업데이트 완료")
            print(f"   업데이트된 종목: {result['updated_count']}개")
            print(f"   총 평가액: {result['total_value']:,.0f}원")
            print(f"   총 평가 손익: {result['total_profit_loss']:+,.0f}원")

    except Exception as e:
        print(f"❌ 오류: {e}")
        sys.exit(1)
