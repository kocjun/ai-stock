"""데이터 품질 체크 Tool"""

from typing import Any
from crewai.tools import BaseTool
from core.utils.db_utils import get_db_connection


class DataQualityTool(BaseTool):
    name: str = "data_quality_checker"
    description: str = """
    수집된 데이터의 품질을 체크하고 통계를 제공합니다.

    사용법:
    - check_all: 전체 데이터 품질 체크
    - check_stocks: 종목 데이터 체크
    - check_prices: 가격 데이터 체크
    - check_coverage: 데이터 커버리지 체크
    """

    def _run(self, command: str = "check_all") -> str:
        """데이터 품질 체크 실행"""
        try:
            command = command.strip().lower()

            if command == "check_all":
                return self._check_all()
            elif command == "check_stocks":
                return self._check_stocks()
            elif command == "check_prices":
                return self._check_prices()
            elif command == "check_coverage":
                return self._check_coverage()
            else:
                return "알 수 없는 명령입니다. check_all, check_stocks, check_prices, check_coverage 중 하나를 사용하세요."

        except Exception as e:
            return f"데이터 품질 체크 중 오류 발생: {str(e)}"

    def _check_all(self) -> str:
        """전체 데이터 품질 체크"""
        result = []
        result.append("=" * 60)
        result.append("데이터 품질 체크 결과")
        result.append("=" * 60)

        conn = get_db_connection()
        cur = conn.cursor()

        # 1. 종목 수
        cur.execute("SELECT COUNT(*) FROM stocks;")
        stock_count = cur.fetchone()[0]
        result.append(f"종목 수: {stock_count:,}개")

        # 2. 가격 데이터 수
        cur.execute("SELECT COUNT(*) FROM prices;")
        price_count = cur.fetchone()[0]
        result.append(f"가격 데이터: {price_count:,} rows")

        # 3. 날짜 범위
        cur.execute("SELECT MIN(date), MAX(date) FROM prices;")
        date_range = cur.fetchone()
        if date_range[0]:
            result.append(f"날짜 범위: {date_range[0]} ~ {date_range[1]}")

        # 4. 시장별 종목 수
        cur.execute("""
            SELECT market, COUNT(*) as cnt
            FROM stocks
            GROUP BY market
            ORDER BY cnt DESC;
        """)
        markets = cur.fetchall()
        result.append("\n시장별 종목 수:")
        for market, cnt in markets:
            result.append(f"  {market}: {cnt}개")

        # 5. 섹터별 종목 수 (상위 5개)
        cur.execute("""
            SELECT sector, COUNT(*) as cnt
            FROM stocks
            WHERE sector IS NOT NULL AND sector != 'N/A'
            GROUP BY sector
            ORDER BY cnt DESC
            LIMIT 5;
        """)
        sectors = cur.fetchall()
        if sectors:
            result.append("\n섹터별 종목 수 (상위 5개):")
            for sector, cnt in sectors:
                result.append(f"  {sector}: {cnt}개")

        # 6. 데이터 커버리지
        cur.execute("""
            SELECT
                COUNT(DISTINCT s.code) as total_stocks,
                COUNT(DISTINCT p.code) as stocks_with_prices,
                ROUND(COUNT(DISTINCT p.code)::NUMERIC / NULLIF(COUNT(DISTINCT s.code), 0) * 100, 2) as coverage
            FROM stocks s
            LEFT JOIN prices p ON s.code = p.code;
        """)
        coverage = cur.fetchone()
        result.append(f"\n데이터 커버리지:")
        result.append(f"  전체 종목: {coverage[0]}개")
        result.append(f"  가격 데이터 있음: {coverage[1]}개")
        result.append(f"  커버리지: {coverage[2]}%")

        # 7. 데이터 품질 이슈
        cur.execute("""
            SELECT COUNT(*)
            FROM prices
            WHERE close <= 0 OR volume < 0;
        """)
        invalid_count = cur.fetchone()[0]
        if invalid_count > 0:
            result.append(f"\n⚠ 품질 이슈: {invalid_count}개 행에 비정상 값 존재")
        else:
            result.append("\n✓ 데이터 품질: 정상")

        cur.close()
        conn.close()

        result.append("=" * 60)
        return "\n".join(result)

    def _check_stocks(self) -> str:
        """종목 데이터 체크"""
        conn = get_db_connection()
        cur = conn.cursor()

        result = []
        result.append("종목 데이터 체크:")

        cur.execute("SELECT COUNT(*), COUNT(DISTINCT code) FROM stocks;")
        total, unique = cur.fetchone()
        result.append(f"  총 {total}개 (중복: {total - unique}개)")

        cur.execute("SELECT COUNT(*) FROM stocks WHERE name IS NULL OR name = '';")
        null_names = cur.fetchone()[0]
        if null_names > 0:
            result.append(f"  ⚠ 이름 없음: {null_names}개")

        cur.close()
        conn.close()

        return "\n".join(result)

    def _check_prices(self) -> str:
        """가격 데이터 체크"""
        conn = get_db_connection()
        cur = conn.cursor()

        result = []
        result.append("가격 데이터 체크:")

        cur.execute("SELECT COUNT(*) FROM prices;")
        total = cur.fetchone()[0]
        result.append(f"  총 {total:,} rows")

        cur.execute("SELECT COUNT(*) FROM prices WHERE close <= 0;")
        invalid_price = cur.fetchone()[0]
        if invalid_price > 0:
            result.append(f"  ⚠ 비정상 가격: {invalid_price}개")

        cur.execute("SELECT COUNT(*) FROM prices WHERE volume < 0;")
        invalid_volume = cur.fetchone()[0]
        if invalid_volume > 0:
            result.append(f"  ⚠ 비정상 거래량: {invalid_volume}개")

        cur.close()
        conn.close()

        return "\n".join(result)

    def _check_coverage(self) -> str:
        """데이터 커버리지 체크"""
        conn = get_db_connection()
        cur = conn.cursor()

        result = []
        result.append("데이터 커버리지:")

        cur.execute("""
            SELECT
                s.code,
                s.name,
                COUNT(p.date) as price_count
            FROM stocks s
            LEFT JOIN prices p ON s.code = p.code
            GROUP BY s.code, s.name
            HAVING COUNT(p.date) = 0
            LIMIT 10;
        """)
        missing = cur.fetchall()

        if missing:
            result.append(f"\n  가격 데이터 없는 종목 (최대 10개):")
            for code, name, _ in missing:
                result.append(f"    - {name} ({code})")
        else:
            result.append("\n  ✓ 모든 종목에 가격 데이터 존재")

        cur.close()
        conn.close()

        return "\n".join(result)
