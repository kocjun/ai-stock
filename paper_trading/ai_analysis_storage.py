"""
AI 분석 결과 저장 및 조회 모듈

CrewAI가 생성한 AI 분석 결과를 구조화된 형식으로 데이터베이스에 저장
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import logging

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from core.utils.db_utils import get_db_connection

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AIAnalysisStorage:
    """AI 분석 결과 저장 및 관리 클래스"""

    @staticmethod
    def save_stock_analysis(
        code: str,
        overall_score: float,
        financial_score: float,
        technical_score: float,
        risk_score: float,
        target_price: float,
        target_horizon_days: int,
        confidence_level: float,
        risk_grade: str,
        volatility: float,
        max_drawdown: float,
        buy_rationale: str,
        key_factors: Dict[str, Any] = None,
        technical_indicators: Dict[str, Any] = None,
        financial_metrics: Dict[str, Any] = None,
        analysis_source: str = 'integrated_crew'
    ) -> Optional[int]:
        """
        AI 종목 분석 결과 저장

        Args:
            code: 종목 코드
            overall_score: 종합 점수 (0-100)
            financial_score: 재무 점수
            technical_score: 기술적 점수
            risk_score: 리스크 점수
            target_price: 목표가
            target_horizon_days: 목표 기간 (일)
            confidence_level: 신뢰도 (0-100)
            risk_grade: 리스크 등급 ('Low', 'Medium', 'High')
            volatility: 변동성
            max_drawdown: 최대 낙폭
            buy_rationale: 매수 근거 텍스트
            key_factors: 핵심 요인 딕셔너리
            technical_indicators: 기술적 지표 딕셔너리
            financial_metrics: 재무 지표 딕셔너리
            analysis_source: 분석 출처

        Returns:
            int: 저장된 분석 ID (실패시 None)
        """
        conn = get_db_connection()
        cur = conn.cursor()

        try:
            # JSON 데이터 직렬화
            key_factors_json = json.dumps(key_factors or {})
            technical_indicators_json = json.dumps(technical_indicators or {})
            financial_metrics_json = json.dumps(financial_metrics or {})

            cur.execute("""
                INSERT INTO ai_stock_analysis (
                    code, overall_score, financial_score, technical_score, risk_score,
                    target_price, target_horizon_days, confidence_level,
                    risk_grade, volatility, max_drawdown,
                    buy_rationale, key_factors, technical_indicators, financial_metrics,
                    analysis_source
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING analysis_id
            """, (
                code, overall_score, financial_score, technical_score, risk_score,
                target_price, target_horizon_days, confidence_level,
                risk_grade, volatility, max_drawdown,
                buy_rationale, key_factors_json, technical_indicators_json,
                financial_metrics_json, analysis_source
            ))

            analysis_id = cur.fetchone()[0]
            conn.commit()

            logger.info(f"✓ AI 분석 저장: {code} (Analysis ID: {analysis_id})")
            return analysis_id

        except Exception as e:
            conn.rollback()
            logger.error(f"✗ AI 분석 저장 실패 ({code}): {e}")
            return None

        finally:
            cur.close()
            conn.close()

    @staticmethod
    def link_trade_to_analysis(
        trade_id: int,
        analysis_id: int,
        influence_score: float = None
    ) -> bool:
        """
        거래와 AI 분석 연결

        Args:
            trade_id: 거래 ID
            analysis_id: 분석 ID
            influence_score: 영향도 점수 (0-100)

        Returns:
            bool: 성공 여부
        """
        conn = get_db_connection()
        cur = conn.cursor()

        try:
            cur.execute("""
                INSERT INTO trade_ai_analysis (trade_id, analysis_id, influence_score)
                VALUES (%s, %s, %s)
                ON CONFLICT (trade_id, analysis_id) DO NOTHING
            """, (trade_id, analysis_id, influence_score))

            conn.commit()
            logger.info(f"✓ 거래-분석 연결: Trade {trade_id} ← Analysis {analysis_id}")
            return True

        except Exception as e:
            conn.rollback()
            logger.error(f"✗ 거래-분석 연결 실패: {e}")
            return False

        finally:
            cur.close()
            conn.close()

    @staticmethod
    def save_portfolio_insight(
        account_id: int,
        expected_return: float,
        expected_volatility: float,
        sharpe_ratio: float,
        market_sentiment: str,
        rebalance_needed: bool,
        market_analysis: str,
        sector_allocation: Dict[str, float] = None,
        portfolio_analysis: str = None,
        recommendations: str = None
    ) -> Optional[int]:
        """
        포트폴리오 AI 인사이트 저장

        Args:
            account_id: 계좌 ID
            expected_return: 기대 수익률
            expected_volatility: 기대 변동성
            sharpe_ratio: 샤프 비율
            market_sentiment: 시장 전망 ('Bearish', 'Neutral', 'Bullish')
            rebalance_needed: 리밸런싱 필요 여부
            market_analysis: 시장 분석 텍스트
            sector_allocation: 섹터별 배분
            portfolio_analysis: 포트폴리오 분석
            recommendations: 추천사항

        Returns:
            int: 저장된 인사이트 ID (실패시 None)
        """
        conn = get_db_connection()
        cur = conn.cursor()

        try:
            sector_allocation_json = json.dumps(sector_allocation or {})

            cur.execute("""
                INSERT INTO portfolio_ai_insights (
                    account_id, expected_return, expected_volatility, sharpe_ratio,
                    market_sentiment, rebalance_needed, market_analysis,
                    sector_allocation, portfolio_analysis, recommendations
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING insight_id
            """, (
                account_id, expected_return, expected_volatility, sharpe_ratio,
                market_sentiment, rebalance_needed, market_analysis,
                sector_allocation_json, portfolio_analysis, recommendations
            ))

            insight_id = cur.fetchone()[0]
            conn.commit()

            logger.info(f"✓ 포트폴리오 인사이트 저장: Account {account_id} (Insight ID: {insight_id})")
            return insight_id

        except Exception as e:
            conn.rollback()
            logger.error(f"✗ 포트폴리오 인사이트 저장 실패: {e}")
            return None

        finally:
            cur.close()
            conn.close()

    @staticmethod
    def get_stock_analysis(code: str, limit: int = 1) -> List[Dict]:
        """
        종목의 최신 AI 분석 조회

        Args:
            code: 종목 코드
            limit: 조회할 분석 개수

        Returns:
            List[Dict]: AI 분석 결과 리스트
        """
        conn = get_db_connection()
        cur = conn.cursor()

        try:
            cur.execute("""
                SELECT
                    analysis_id, code, analysis_date,
                    overall_score, financial_score, technical_score, risk_score,
                    target_price, target_horizon_days, confidence_level,
                    risk_grade, volatility, max_drawdown,
                    buy_rationale, key_factors, technical_indicators, financial_metrics
                FROM ai_stock_analysis
                WHERE code = %s
                ORDER BY analysis_date DESC
                LIMIT %s
            """, (code, limit))

            columns = [desc[0] for desc in cur.description]
            results = []

            for row in cur.fetchall():
                result = dict(zip(columns, row))
                # JSON 필드 파싱
                result['key_factors'] = json.loads(result['key_factors']) if result['key_factors'] else {}
                result['technical_indicators'] = json.loads(result['technical_indicators']) if result['technical_indicators'] else {}
                result['financial_metrics'] = json.loads(result['financial_metrics']) if result['financial_metrics'] else {}
                results.append(result)

            return results

        except Exception as e:
            logger.error(f"✗ 분석 조회 실패 ({code}): {e}")
            return []

        finally:
            cur.close()
            conn.close()

    @staticmethod
    def get_portfolio_ai_summary(account_id: int) -> Optional[Dict]:
        """
        포트폴리오의 최신 AI 인사이트 조회

        Args:
            account_id: 계좌 ID

        Returns:
            Dict: AI 인사이트 정보 (없으면 None)
        """
        conn = get_db_connection()
        cur = conn.cursor()

        try:
            cur.execute("""
                SELECT
                    insight_id, account_id, insight_date,
                    expected_return, expected_volatility, sharpe_ratio,
                    market_sentiment, rebalance_needed, market_analysis,
                    sector_allocation, portfolio_analysis, recommendations
                FROM portfolio_ai_insights
                WHERE account_id = %s
                ORDER BY insight_date DESC
                LIMIT 1
            """, (account_id,))

            row = cur.fetchone()
            if not row:
                return None

            columns = [desc[0] for desc in cur.description]
            result = dict(zip(columns, row))

            # JSON 필드 파싱
            result['sector_allocation'] = json.loads(result['sector_allocation']) if result['sector_allocation'] else {}

            return result

        except Exception as e:
            logger.error(f"✗ 포트폴리오 인사이트 조회 실패: {e}")
            return None

        finally:
            cur.close()
            conn.close()

    @staticmethod
    def get_holding_analysis(account_id: int) -> List[Dict]:
        """
        보유 종목의 최신 AI 분석 조회

        Args:
            account_id: 계좌 ID

        Returns:
            List[Dict]: 보유 종목별 AI 분석 결과
        """
        conn = get_db_connection()
        cur = conn.cursor()

        try:
            cur.execute("""
                SELECT
                    p.code, p.quantity, p.avg_price, p.current_price, p.profit_loss_pct,
                    a.analysis_id, a.overall_score, a.financial_score, a.technical_score,
                    a.target_price, a.confidence_level, a.risk_grade,
                    a.buy_rationale, a.key_factors, a.technical_indicators, a.analysis_date
                FROM virtual_portfolio p
                LEFT JOIN LATERAL (
                    SELECT *
                    FROM ai_stock_analysis
                    WHERE code = p.code
                    ORDER BY analysis_date DESC
                    LIMIT 1
                ) a ON TRUE
                WHERE p.account_id = %s AND p.quantity > 0
                ORDER BY p.current_value DESC
            """, (account_id,))

            columns = [desc[0] for desc in cur.description]
            results = []

            for row in cur.fetchall():
                result = dict(zip(columns, row))
                if result['key_factors']:
                    result['key_factors'] = json.loads(result['key_factors'])
                if result['technical_indicators']:
                    result['technical_indicators'] = json.loads(result['technical_indicators'])
                results.append(result)

            return results

        except Exception as e:
            logger.error(f"✗ 보유 종목 분석 조회 실패: {e}")
            return []

        finally:
            cur.close()
            conn.close()

    @staticmethod
    def get_high_score_stocks(
        min_score: float = 70,
        limit: int = 10
    ) -> List[Dict]:
        """
        높은 점수의 종목 조회

        Args:
            min_score: 최소 점수 기준
            limit: 조회 개수

        Returns:
            List[Dict]: 높은 점수 종목 리스트
        """
        conn = get_db_connection()
        cur = conn.cursor()

        try:
            cur.execute("""
                SELECT
                    code, overall_score, financial_score, technical_score, risk_score,
                    target_price, confidence_level, risk_grade,
                    buy_rationale, analysis_date
                FROM ai_stock_analysis
                WHERE overall_score >= %s
                ORDER BY analysis_date DESC, overall_score DESC
                LIMIT %s
            """, (min_score, limit))

            columns = [desc[0] for desc in cur.description]
            results = [dict(zip(columns, row)) for row in cur.fetchall()]

            return results

        except Exception as e:
            logger.error(f"✗ 높은 점수 종목 조회 실패: {e}")
            return []

        finally:
            cur.close()
            conn.close()


# 편의 함수들

def save_stock_ai_analysis(**kwargs) -> Optional[int]:
    """AI 종목 분석 저장 (편의 함수)"""
    return AIAnalysisStorage.save_stock_analysis(**kwargs)


def save_portfolio_ai_insight(**kwargs) -> Optional[int]:
    """포트폴리오 AI 인사이트 저장 (편의 함수)"""
    return AIAnalysisStorage.save_portfolio_insight(**kwargs)


def get_stock_analysis(code: str, limit: int = 1) -> List[Dict]:
    """종목 AI 분석 조회 (편의 함수)"""
    return AIAnalysisStorage.get_stock_analysis(code, limit)


def get_holding_analysis(account_id: int) -> List[Dict]:
    """보유 종목 AI 분석 조회 (편의 함수)"""
    return AIAnalysisStorage.get_holding_analysis(account_id)


def get_portfolio_ai_summary(account_id: int) -> Optional[Dict]:
    """포트폴리오 AI 인사이트 조회 (편의 함수)"""
    return AIAnalysisStorage.get_portfolio_ai_summary(account_id)


if __name__ == "__main__":
    # 테스트 예제
    print("AI Analysis Storage Module Test\n")

    # 테스트 데이터
    test_analysis = {
        'code': '005930',
        'overall_score': 78.5,
        'financial_score': 75.0,
        'technical_score': 82.0,
        'risk_score': 65.0,
        'target_price': 120000,
        'target_horizon_days': 90,
        'confidence_level': 85.0,
        'risk_grade': 'Medium',
        'volatility': 15.2,
        'max_drawdown': 12.5,
        'buy_rationale': '반도체 업황 회복, HBM 수요 증가, PER 저평가',
        'key_factors': {
            'trend': 'Positive',
            'earnings': 'Growing',
            'valuation': 'Cheap'
        },
        'technical_indicators': {
            'RSI': 52,
            'MACD': 'Golden Cross',
            'MA20': 'Uptrend'
        },
        'financial_metrics': {
            'PER': 10.5,
            'PBR': 1.2,
            'ROE': 15.5
        }
    }

    # 분석 저장
    print("1. Saving stock analysis...")
    analysis_id = save_stock_ai_analysis(**test_analysis)
    print(f"   ✓ Analysis ID: {analysis_id}\n")

    # 분석 조회
    print("2. Retrieving stock analysis...")
    analyses = get_stock_analysis('005930')
    if analyses:
        print(f"   ✓ Found {len(analyses)} analysis record(s)")
        print(f"   Overall Score: {analyses[0]['overall_score']}")
        print(f"   Target Price: {analyses[0]['target_price']:,.0f}원\n")

    # 높은 점수 종목 조회
    print("3. Getting high-score stocks...")
    high_scores = AIAnalysisStorage.get_high_score_stocks(min_score=70, limit=5)
    print(f"   ✓ Found {len(high_scores)} high-score stock(s)\n")
