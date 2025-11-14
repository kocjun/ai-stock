"""
가격 자동 업데이트 모듈

매일 장 마감 후 최신 주식 가격을 수집하여 데이터베이스에 저장
FinanceDataReader 활용
"""

import sys
from pathlib import Path
from typing import List, Optional
from datetime import datetime, date
import logging

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from core.utils.db_utils import get_db_connection

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/Users/yeongchang.jeon/workspace/ai-agent/paper_trading/logs/price_updater.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def get_portfolio_stocks(account_id: int = 1) -> List[str]:
    """
    포트폴리오에 보유 중인 종목 코드 조회

    Args:
        account_id: 계좌 ID

    Returns:
        List[str]: 종목 코드 리스트
    """
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT DISTINCT code
            FROM virtual_portfolio
            WHERE account_id = %s AND quantity > 0
            ORDER BY code
        """, (account_id,))

        return [row[0] for row in cur.fetchall()]

    except Exception as e:
        logger.error(f"포트폴리오 종목 조회 실패: {e}")
        return []

    finally:
        cur.close()
        conn.close()


def fetch_price_data(codes: List[str]) -> dict:
    """
    FinanceDataReader에서 주가 데이터 수집

    Args:
        codes: 종목 코드 리스트

    Returns:
        dict: {코드: {'date': date, 'close': float, 'volume': int, 'high': float, 'low': float}}
    """
    try:
        import FinanceDataReader as fdr
    except ImportError:
        logger.error("FinanceDataReader 설치 필요: pip install FinanceDatareader")
        return {}

    price_data = {}

    for code in codes:
        try:
            # 코드 포맷: KOSPI는 숫자만 (005930), KOSDAQ는 Q+숫자 (A005380)
            ticker = code if code.startswith('Q') else code

            # 최근 1일 데이터 수집
            df = fdr.DataReader(ticker, start=date.today(), end=date.today())

            if df is not None and not df.empty:
                latest = df.iloc[-1]

                price_data[code] = {
                    'date': df.index[-1].date() if hasattr(df.index[-1], 'date') else date.today(),
                    'close': float(latest['Close']),
                    'high': float(latest['High']),
                    'low': float(latest['Low']),
                    'volume': int(latest['Volume']) if 'Volume' in latest else 0,
                }
                logger.info(f"✓ {code}: {price_data[code]['close']:,.0f}원")

            else:
                logger.warning(f"✗ {code}: 데이터 없음 (장 마감 전 또는 거래정지)")

        except Exception as e:
            logger.warning(f"✗ {code}: 수집 실패 - {str(e)[:100]}")
            continue

    return price_data


def update_price_to_db(price_data: dict, account_id: int = 1) -> int:
    """
    수집한 가격 데이터를 데이터베이스에 저장

    Args:
        price_data: 가격 데이터 딕셔너리
        account_id: 계좌 ID

    Returns:
        int: 업데이트된 행 수
    """
    conn = get_db_connection()
    cur = conn.cursor()
    updated_count = 0

    try:
        for code, data in price_data.items():
            try:
                # prices 테이블에 저장
                cur.execute("""
                    INSERT INTO prices (code, date, close, high, low, volume)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (code, date) DO UPDATE SET
                        close = EXCLUDED.close,
                        high = EXCLUDED.high,
                        low = EXCLUDED.low,
                        volume = EXCLUDED.volume
                """, (
                    code,
                    data['date'],
                    data['close'],
                    data['high'],
                    data['low'],
                    data['volume']
                ))

                # virtual_portfolio의 current_price 업데이트
                cur.execute("""
                    UPDATE virtual_portfolio
                    SET current_price = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE account_id = %s AND code = %s
                """, (data['close'], account_id, code))

                updated_count += 1

            except Exception as e:
                logger.error(f"DB 저장 실패 ({code}): {e}")
                continue

        conn.commit()
        logger.info(f"데이터베이스 업데이트 완료: {updated_count}개 종목")

    except Exception as e:
        conn.rollback()
        logger.error(f"트랜잭션 오류: {e}")
        return 0

    finally:
        cur.close()
        conn.close()

    return updated_count


def update_portfolio_values(account_id: int = 1) -> dict:
    """
    포트폴리오 평가액 및 손익 업데이트

    Args:
        account_id: 계좌 ID

    Returns:
        dict: 업데이트 결과 요약
    """
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # virtual_portfolio의 평가액, 손익 계산
        cur.execute("""
            UPDATE virtual_portfolio
            SET
                current_value = quantity * current_price,
                profit_loss = (quantity * current_price) - (quantity * avg_price),
                profit_loss_pct = CASE WHEN avg_price > 0 THEN ((current_price - avg_price) / avg_price * 100) ELSE 0 END,
                updated_at = CURRENT_TIMESTAMP
            WHERE account_id = %s AND quantity > 0
        """, (account_id,))

        affected_rows = cur.rowcount

        # 포트폴리오 전체 평가액 업데이트
        cur.execute("""
            SELECT
                COALESCE(SUM(current_value), 0) as stock_value,
                COALESCE(SUM(profit_loss), 0) as total_profit_loss
            FROM virtual_portfolio
            WHERE account_id = %s AND quantity > 0
        """, (account_id,))

        stock_value, total_profit_loss = cur.fetchone()

        # 계좌 정보 업데이트 (기존 컬럼만 사용)
        # 주석: virtual_accounts 테이블에는 stock_value, total_value, total_return 등의 컬럼이 없으므로
        # virtual_portfolio_history에 스냅샷을 저장하는 방식으로 대체
        try:
            cur.execute("""
                INSERT INTO virtual_portfolio_history
                    (account_id, snapshot_date, total_value, cash_balance, stock_value, return_pct)
                SELECT
                    a.account_id,
                    CURRENT_DATE,
                    a.current_balance + %s,
                    a.current_balance,
                    %s,
                    ((a.current_balance + %s - a.initial_balance) / a.initial_balance * 100)
                FROM virtual_accounts a
                WHERE a.account_id = %s
                ON CONFLICT (account_id, snapshot_date) DO UPDATE SET
                    total_value = EXCLUDED.total_value,
                    cash_balance = EXCLUDED.cash_balance,
                    stock_value = EXCLUDED.stock_value,
                    return_pct = EXCLUDED.return_pct,
                    created_at = CURRENT_TIMESTAMP
            """, (stock_value, stock_value, stock_value, account_id))
        except Exception as e:
            logger.warning(f"포트폴리오 히스토리 저장 실패: {e}")

        conn.commit()

        logger.info(f"포트폴리오 평가액 업데이트: {affected_rows}개 종목")
        logger.info(f"총 주식 평가액: {stock_value:,.0f}원, 평가 손익: {total_profit_loss:,.0f}원")

        return {
            'updated_positions': affected_rows,
            'stock_value': float(stock_value),
            'total_profit_loss': float(total_profit_loss)
        }

    except Exception as e:
        conn.rollback()
        logger.error(f"포트폴리오 업데이트 실패: {e}")
        return {'updated_positions': 0, 'stock_value': 0, 'total_profit_loss': 0}

    finally:
        cur.close()
        conn.close()


def run_price_update(account_id: int = 1) -> dict:
    """
    주가 업데이트 메인 함수

    Args:
        account_id: 계좌 ID

    Returns:
        dict: 업데이트 결과 요약
    """
    logger.info("=" * 60)
    logger.info("가격 업데이트 시작")
    logger.info("=" * 60)

    # 1. 포트폴리오 종목 조회
    codes = get_portfolio_stocks(account_id)
    if not codes:
        logger.warning("보유 종목이 없습니다")
        return {'status': 'no_positions', 'updated_count': 0}

    logger.info(f"보유 종목: {codes}")

    # 2. 가격 데이터 수집
    price_data = fetch_price_data(codes)
    if not price_data:
        logger.warning("수집된 가격 데이터가 없습니다")
        return {'status': 'no_data', 'updated_count': 0}

    # 3. 데이터베이스 업데이트
    updated_count = update_price_to_db(price_data, account_id)

    # 4. 포트폴리오 평가액 업데이트
    portfolio_result = update_portfolio_values(account_id)

    logger.info("=" * 60)
    logger.info(f"가격 업데이트 완료: {updated_count}개 종목")
    logger.info("=" * 60)

    return {
        'status': 'success',
        'updated_count': updated_count,
        **portfolio_result
    }


if __name__ == "__main__":
    # 직접 실행 시
    result = run_price_update(account_id=1)
    print(f"\n업데이트 결과: {result}")
