"""
섹터별 주도주 탐지 모듈

각 섹터에서 시장을 주도하는 상위 종목을 자동으로 탐지합니다.
주도주는 시가총액, 유동성, 기술적 모멘텀, 재무 건전성, 안정성을 고려하여 선정됩니다.
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
import pandas as pd
import numpy as np

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from core.utils.db_utils import get_db_connection
from core.modules.financial_metrics import calculate_basic_ratios

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class SectorLeaderConfig:
    """섹터 주도주 탐지 설정"""
    leaders_per_sector: int = 2  # 섹터당 주도주 개수
    min_trading_amount: float = 50_000_000_000  # 최소 거래대금 (500억)
    min_market_cap: float = 1_000_000_000_000  # 최소 시가총액 (1조)
    max_volatility: float = 50.0  # 최대 변동성 (%)
    analysis_days: int = 60  # 분석 기간 (일)

    # 가중치 (합계: 100%)
    market_cap_weight: float = 0.35  # 시가총액: 35%
    trading_amount_weight: float = 0.25  # 거래대금: 25%
    momentum_weight: float = 0.20  # 모멘텀: 20%
    financial_weight: float = 0.15  # 재무 건전성: 15%
    stability_weight: float = 0.05  # 안정성: 5%


class SectorLeaderDetector:
    """섹터별 주도주 탐지 클래스"""

    def __init__(self, config: Optional[SectorLeaderConfig] = None):
        """
        초기화

        Args:
            config: 탐지 설정 (None이면 기본값 사용)
        """
        self.config = config or SectorLeaderConfig()
        self.conn = None

    def detect_leaders(self, market: str = "KOSPI") -> Dict[str, List[Dict]]:
        """
        섹터별 주도주 탐지

        Args:
            market: 시장 (KOSPI 또는 KOSDAQ)

        Returns:
            Dict: 섹터별 주도주 목록
                {
                    "반도체/전기전자": [
                        {"code": "005930", "name": "삼성전자", "leadership_score": 95.5, ...},
                        {"code": "000660", "name": "SK하이닉스", "leadership_score": 88.3, ...}
                    ],
                    ...
                }
        """
        try:
            logger.info("=" * 60)
            logger.info(f"섹터별 주도주 탐지 시작 ({market})")
            logger.info("=" * 60)

            # 시장의 모든 종목 조회
            stocks_df = self._get_market_stocks(market)
            if stocks_df.empty:
                logger.warning(f"시장 {market}의 종목 데이터를 찾을 수 없습니다")
                return {}

            logger.info(f"총 {len(stocks_df)}개 종목 로드")

            # 섹터별 그룹화
            results = {}
            sectors = stocks_df['sector'].unique()

            for sector in sectors:
                if pd.isna(sector):
                    continue

                logger.info(f"\n▶ {sector} 분석 중...")
                sector_stocks = stocks_df[stocks_df['sector'] == sector].copy()

                if sector_stocks.empty:
                    logger.warning(f"  {sector}의 종목 데이터 없음")
                    continue

                # 섹터별 주도주 탐지
                leaders = self._detect_sector_leaders(sector_stocks)

                if leaders:
                    results[sector] = leaders
                    logger.info(f"  ✓ {sector}: {len(leaders)}개 주도주 탐지")

            logger.info("\n" + "=" * 60)
            logger.info(f"주도주 탐지 완료: {sum(len(v) for v in results.values())}개 종목")
            logger.info("=" * 60)

            return results

        except Exception as e:
            logger.error(f"주도주 탐지 실패: {e}", exc_info=True)
            return {}

    def _detect_sector_leaders(self, sector_stocks: pd.DataFrame) -> List[Dict]:
        """
        특정 섹터의 주도주 탐지

        Args:
            sector_stocks: 섹터 내 종목 DataFrame

        Returns:
            List[Dict]: 주도주 목록 (점수 내림차순)
        """
        leaders = []

        for _, stock in sector_stocks.iterrows():
            try:
                code = stock['code']
                name = stock['name']

                # 각 종목의 주도주 점수 계산
                score_result = self._calculate_leadership_score(code, name, stock)

                if score_result and score_result['total_score'] > 0:
                    leaders.append(score_result)

            except Exception as e:
                logger.warning(f"  ⚠️  {stock.get('name', code)} 분석 실패: {str(e)[:50]}")
                continue

        # 점수 순으로 정렬
        leaders.sort(key=lambda x: x['total_score'], reverse=True)

        # 상위 N개만 선택
        return leaders[:self.config.leaders_per_sector]

    def _calculate_leadership_score(
        self, code: str, name: str, stock_info: Dict
    ) -> Optional[Dict]:
        """
        종목의 주도주 점수 계산

        Args:
            code: 종목 코드
            name: 종목명
            stock_info: 종목 기본 정보

        Returns:
            Dict: 점수 분석 결과 또는 None
        """
        try:
            # 1. 시가총액 점수
            market_cap = stock_info.get('market_cap', 0)
            if not market_cap or market_cap < self.config.min_market_cap:
                logger.debug(f"  {name}: 시가총액 미달 (필요: {self.config.min_market_cap:,})")
                return None

            market_cap_score = self._score_market_cap(market_cap)

            # 2. 거래대금 점수
            trading_amount_score, avg_amount = self._score_trading_amount(code)
            if avg_amount < self.config.min_trading_amount:
                logger.debug(f"  {name}: 거래대금 미달 (필요: {self.config.min_trading_amount:,})")
                return None

            # 3. 모멘텀 점수
            momentum_score = self._score_momentum(code)

            # 4. 재무 건전성 점수
            financial_score = self._score_financial_health(code)

            # 5. 안정성 점수
            stability_score = self._score_stability(code)

            # 종합 점수 계산
            total_score = (
                market_cap_score * self.config.market_cap_weight +
                trading_amount_score * self.config.trading_amount_weight +
                momentum_score * self.config.momentum_weight +
                financial_score * self.config.financial_weight +
                stability_score * self.config.stability_weight
            )

            return {
                'code': code,
                'name': name,
                'sector': stock_info.get('sector', 'Unknown'),
                'total_score': round(total_score, 2),
                'market_cap_score': round(market_cap_score, 2),
                'trading_amount_score': round(trading_amount_score, 2),
                'momentum_score': round(momentum_score, 2),
                'financial_score': round(financial_score, 2),
                'stability_score': round(stability_score, 2),
                'market_cap': market_cap,
                'avg_trading_amount': round(avg_amount, 0),
            }

        except Exception as e:
            logger.debug(f"  {name} 점수 계산 실패: {e}")
            return None

    def _score_market_cap(self, market_cap: float) -> float:
        """
        시가총액 점수 (0-100)

        큰 시가총액일수록 높은 점수
        """
        # 시가총액 범위: 1조 ~ 100조
        min_cap = 1_000_000_000_000  # 1조
        max_cap = 100_000_000_000_000  # 100조

        if market_cap < min_cap:
            return 0.0

        # 로그 스케일로 정규화
        normalized = (np.log(market_cap) - np.log(min_cap)) / (np.log(max_cap) - np.log(min_cap))
        return min(max(normalized * 100, 0), 100)

    def _score_trading_amount(self, code: str) -> Tuple[float, float]:
        """
        거래대금 점수 (0-100)

        높은 거래대금과 안정적인 거래량일수록 높은 점수

        Returns:
            Tuple[float, float]: (점수, 평균 거래대금)
        """
        try:
            conn = get_db_connection()
            cur = conn.cursor()

            # 최근 거래 데이터 조회
            cur.execute("""
                SELECT
                    DATE(date) as trade_date,
                    SUM(close * volume) as daily_amount
                FROM prices
                WHERE code = %s
                AND date >= NOW() - INTERVAL '%s days'
                GROUP BY DATE(date)
                ORDER BY date DESC
                LIMIT %s
            """, (code, self.config.analysis_days, self.config.analysis_days))

            rows = cur.fetchall()
            cur.close()
            conn.close()

            if not rows:
                return 0.0, 0.0

            amounts = [row[1] for row in rows if row[1]]
            if not amounts:
                return 0.0, 0.0

            avg_amount = np.mean(amounts)
            volatility_cv = np.std(amounts) / avg_amount if avg_amount > 0 else 0

            # 기본 점수: 거래대금 기반
            amount_score = min((avg_amount / 100_000_000_000) * 100, 100)  # 100억 기준

            # 안정성 보정: CV가 작을수록 좋음
            stability_penalty = min(volatility_cv * 10, 20)  # 최대 20점 감점

            score = max(amount_score - stability_penalty, 0)

            return score, avg_amount

        except Exception as e:
            logger.debug(f"거래대금 점수 계산 실패 ({code}): {e}")
            return 0.0, 0.0

    def _score_momentum(self, code: str) -> float:
        """
        모멘텀 점수 (0-100)

        최근 가격 상승 추세를 평가
        """
        try:
            conn = get_db_connection()
            cur = conn.cursor()

            # 최근 30일 가격 데이터
            cur.execute("""
                SELECT date, close
                FROM prices
                WHERE code = %s
                AND date >= NOW() - INTERVAL '30 days'
                ORDER BY date ASC
                LIMIT 30
            """, (code,))

            rows = cur.fetchall()
            cur.close()
            conn.close()

            if len(rows) < 10:
                return 50.0  # 데이터 부족시 중립

            closes = [row[1] for row in rows]

            # 수익률 계산
            returns = [(closes[i] - closes[i - 1]) / closes[i - 1] * 100 for i in range(1, len(closes))]
            avg_return = np.mean(returns) if returns else 0

            # 5일 vs 30일 평균 비교
            sma_5 = np.mean(closes[-5:])
            sma_30 = np.mean(closes)

            momentum_score = 50  # 기본값

            # 단기 상승 추세
            if sma_5 > sma_30 * 1.02:
                momentum_score = 80
            elif sma_5 > sma_30:
                momentum_score = 65
            elif sma_5 < sma_30 * 0.98:
                momentum_score = 30
            else:
                momentum_score = 50

            return momentum_score

        except Exception as e:
            logger.debug(f"모멘텀 점수 계산 실패 ({code}): {e}")
            return 50.0

    def _score_financial_health(self, code: str) -> float:
        """
        재무 건전성 점수 (0-100)

        ROE, 부채비율, 이익 마진을 평가
        """
        try:
            result = calculate_basic_ratios(code)

            if not result or result.get('status') != 'success':
                return 50.0

            score = 50  # 기본값

            # ROE 평가 (20점)
            roe = result.get('roe', 0)
            if roe >= 15:
                score += 20
            elif roe >= 10:
                score += 15
            elif roe >= 5:
                score += 10

            # 부채비율 평가 (15점)
            debt_ratio = result.get('debt_ratio', 100)
            if debt_ratio < 50:
                score += 15
            elif debt_ratio < 100:
                score += 10
            elif debt_ratio < 150:
                score += 5

            # 영업이익률 평가 (15점)
            operating_margin = result.get('operating_margin', 0)
            if operating_margin >= 15:
                score += 15
            elif operating_margin >= 10:
                score += 10
            elif operating_margin >= 5:
                score += 5

            return min(score, 100)

        except Exception as e:
            logger.debug(f"재무 점수 계산 실패 ({code}): {e}")
            return 50.0

    def _score_stability(self, code: str) -> float:
        """
        안정성 점수 (0-100)

        변동성과 최대낙폭을 평가
        """
        try:
            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute("""
                SELECT close
                FROM prices
                WHERE code = %s
                AND date >= NOW() - INTERVAL '%s days'
                ORDER BY date ASC
            """, (code, self.config.analysis_days))

            closes = [row[0] for row in cur.fetchall()]
            cur.close()
            conn.close()

            if len(closes) < 10:
                return 50.0

            closes = np.array(closes)

            # 변동성 계산
            returns = np.diff(closes) / closes[:-1]
            volatility = np.std(returns) * np.sqrt(252) * 100  # 연환산 변동성

            # 최대 낙폭 계산
            cummax = np.maximum.accumulate(closes)
            drawdown = (closes - cummax) / cummax * 100
            max_drawdown = np.min(drawdown)

            # 안정성 점수
            score = 50

            # 변동성 평가 (기준: 20%)
            if volatility < 15:
                score += 20
            elif volatility < 25:
                score += 10
            elif volatility < 35:
                score += 0
            else:
                score -= 10

            # 최대낙폭 평가 (기준: -15%)
            if max_drawdown > -10:
                score += 15
            elif max_drawdown > -15:
                score += 10
            elif max_drawdown > -25:
                score += 5

            return min(max(score, 0), 100)

        except Exception as e:
            logger.debug(f"안정성 점수 계산 실패 ({code}): {e}")
            return 50.0

    def _get_market_stocks(self, market: str = "KOSPI") -> pd.DataFrame:
        """
        시장의 모든 종목 조회

        Args:
            market: 시장 (KOSPI 또는 KOSDAQ)

        Returns:
            DataFrame: 종목 목록
        """
        try:
            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute("""
                SELECT
                    code,
                    name,
                    sector,
                    market,
                    COALESCE((
                        SELECT close * 100000  -- 임시 시가총액 추정 (실제는 발행주식수 필요)
                        FROM prices
                        WHERE code = s.code
                        ORDER BY date DESC
                        LIMIT 1
                    ), 0) as market_cap
                FROM stocks s
                WHERE market = %s
                AND status = 'active'
                ORDER BY code
            """, (market,))

            columns = [desc[0] for desc in cur.description]
            data = cur.fetchall()
            cur.close()
            conn.close()

            df = pd.DataFrame(data, columns=columns)
            return df

        except Exception as e:
            logger.error(f"종목 조회 실패: {e}")
            return pd.DataFrame()


def get_sector_leaders(
    market: str = "KOSPI",
    leaders_per_sector: int = 2
) -> Dict[str, List[Dict]]:
    """
    편의 함수: 섹터별 주도주 탐지

    Args:
        market: 시장 (KOSPI 또는 KOSDAQ)
        leaders_per_sector: 섹터당 주도주 개수

    Returns:
        Dict: 섹터별 주도주 목록
    """
    config = SectorLeaderConfig(leaders_per_sector=leaders_per_sector)
    detector = SectorLeaderDetector(config)
    return detector.detect_leaders(market)


if __name__ == "__main__":
    # 테스트
    print("섹터별 주도주 탐지 테스트\n")

    leaders = get_sector_leaders(market="KOSPI", leaders_per_sector=2)

    for sector, stocks in leaders.items():
        print(f"\n📊 {sector}")
        print("-" * 80)

        for stock in stocks:
            print(f"  {stock['name']} ({stock['code']})")
            print(f"    종합점수: {stock['total_score']}")
            print(f"    - 시가총액: {stock['market_cap_score']}")
            print(f"    - 거래대금: {stock['trading_amount_score']}")
            print(f"    - 모멘텀: {stock['momentum_score']}")
            print(f"    - 재무: {stock['financial_score']}")
            print(f"    - 안정성: {stock['stability_score']}")
