"""데이터 수집 Tool - FinanceDataReader 연동"""

from typing import Any
from crewai.tools import BaseTool
import FinanceDataReader as fdr
from datetime import datetime, timedelta
from core.utils.db_utils import (
    insert_stocks_batch,
    insert_prices_batch,
    get_stock_list
)


class DataCollectionTool(BaseTool):
    name: str = "data_collector"
    description: str = """
    한국 주식 시장 데이터를 수집합니다.

    사용법:
    - collect_stocks: 종목 리스트 수집 (예: "collect_stocks KOSPI 100")
    - collect_prices: 가격 데이터 수집 (예: "collect_prices 005930 30")

    입력 형식:
    - "collect_stocks {market} {limit}" - 시장(KOSPI/KOSDAQ)과 종목 수
    - "collect_prices {code} {days}" - 종목코드와 수집 일수
    - "collect_all {market} {limit} {days}" - 전체 수집
    """

    def _run(self, command: str) -> str:
        """데이터 수집 명령 실행"""
        try:
            parts = command.strip().split()
            if len(parts) < 2:
                return "잘못된 명령 형식입니다. 'collect_stocks KOSPI 50' 또는 'collect_all KOSPI 50 30' 형식을 사용하세요."

            action = parts[0]

            if action == "collect_stocks":
                market = parts[1] if len(parts) > 1 else "KOSPI"
                limit = int(parts[2]) if len(parts) > 2 else 50
                return self._collect_stocks(market, limit)

            elif action == "collect_prices":
                code = parts[1] if len(parts) > 1 else None
                days = int(parts[2]) if len(parts) > 2 else 30
                if not code:
                    return "종목 코드를 지정해주세요."
                return self._collect_prices_single(code, days)

            elif action == "collect_all":
                market = parts[1] if len(parts) > 1 else "KOSPI"
                limit = int(parts[2]) if len(parts) > 2 else 50
                days = int(parts[3]) if len(parts) > 3 else 30
                return self._collect_all(market, limit, days)

            else:
                return f"알 수 없는 명령: {action}. collect_stocks, collect_prices, collect_all 중 하나를 사용하세요."

        except Exception as e:
            return f"데이터 수집 중 오류 발생: {str(e)}"

    def _collect_stocks(self, market: str, limit: int) -> str:
        """종목 리스트 수집"""
        try:
            krx_stocks = fdr.StockListing('KRX')

            if market == 'KOSPI':
                stocks = krx_stocks[krx_stocks['Market'] == 'KOSPI']
            elif market == 'KOSDAQ':
                stocks = krx_stocks[krx_stocks['Market'] == 'KOSDAQ']
            else:
                stocks = krx_stocks

            if limit:
                stocks = stocks.head(limit)

            stocks_data = []
            for _, row in stocks.iterrows():
                code = row['Code']
                name = row['Name']
                market_val = row.get('Market', 'UNKNOWN')
                sector = row.get('Sector', row.get('Industry', 'N/A'))
                stocks_data.append((code, name, market_val, sector))

            affected_rows = insert_stocks_batch(stocks_data)

            return f"✓ 종목 리스트 수집 완료: {affected_rows}개 종목 저장 (시장: {market})"

        except Exception as e:
            return f"✗ 종목 리스트 수집 실패: {str(e)}"

    def _collect_prices_single(self, code: str, days: int) -> str:
        """단일 종목 가격 데이터 수집"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)

            df = fdr.DataReader(code, start_date, end_date)

            if len(df) == 0:
                return f"⚠ 종목 {code}: 데이터 없음"

            prices_data = []
            for date, row in df.iterrows():
                prices_data.append((
                    code,
                    date.date(),
                    float(row['Open']),
                    float(row['High']),
                    float(row['Low']),
                    float(row['Close']),
                    int(row['Volume'])
                ))

            insert_prices_batch(prices_data)

            return f"✓ 종목 {code}: {len(df)}개 데이터 수집 완료"

        except Exception as e:
            return f"✗ 종목 {code} 수집 실패: {str(e)}"

    def _collect_all(self, market: str, limit: int, days: int) -> str:
        """종목 + 가격 데이터 전체 수집"""
        result = []

        # 1. 종목 리스트 수집
        stock_result = self._collect_stocks(market, limit)
        result.append(stock_result)

        # 2. 가격 데이터 수집
        try:
            stocks = get_stock_list(limit=limit)
            success_count = 0
            fail_count = 0

            for code, name, sector in stocks:
                try:
                    end_date = datetime.now()
                    start_date = end_date - timedelta(days=days)
                    df = fdr.DataReader(code, start_date, end_date)

                    if len(df) > 0:
                        prices_data = []
                        for date, row in df.iterrows():
                            prices_data.append((
                                code,
                                date.date(),
                                float(row['Open']),
                                float(row['High']),
                                float(row['Low']),
                                float(row['Close']),
                                int(row['Volume'])
                            ))
                        insert_prices_batch(prices_data)
                        success_count += 1
                    else:
                        fail_count += 1
                except:
                    fail_count += 1

            result.append(f"✓ 가격 데이터 수집 완료: 성공 {success_count}개, 실패 {fail_count}개 (기간: 최근 {days}일)")

        except Exception as e:
            result.append(f"✗ 가격 데이터 수집 실패: {str(e)}")

        return "\n".join(result)
