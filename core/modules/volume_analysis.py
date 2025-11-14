"""
거래량 및 유동성 분석 모듈

종목의 거래량, 거래대금, 유동성 지표를 분석하여
대장주 선정에 필요한 거래량 점수를 계산합니다.
"""

import os
import psycopg2
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta


class VolumeAnalyzer:
    """거래량 및 유동성 분석"""

    def __init__(self):
        self.conn = None

    def get_db_connection(self):
        """PostgreSQL 연결 생성"""
        if self.conn is None or self.conn.closed:
            self.conn = psycopg2.connect(
                host=os.getenv("DB_HOST", "localhost"),
                port=os.getenv("DB_PORT", "5432"),
                database=os.getenv("DB_NAME", "investment_db"),
                user=os.getenv("DB_USER", "invest_user"),
                password=os.getenv("DB_PASSWORD", "invest_pass_2024!")
            )
        return self.conn

    def get_price_data(self, stock_code: str, days: int = 60) -> pd.DataFrame:
        """
        종목의 가격 데이터 조회

        Args:
            stock_code: 종목 코드
            days: 조회 일수

        Returns:
            DataFrame with columns: date, open, high, low, close, volume
        """
        conn = self.get_db_connection()

        query = """
            SELECT
                date,
                open,
                high,
                low,
                close,
                volume
            FROM prices
            WHERE code = %s
            ORDER BY date DESC
            LIMIT %s
        """

        df = pd.read_sql_query(query, conn, params=(stock_code, days))

        if len(df) == 0:
            return pd.DataFrame()

        # 날짜순으로 정렬 (오래된 것부터)
        df = df.sort_values('date').reset_index(drop=True)

        return df

    def analyze_volume(self, stock_code: str, days: int = 60) -> Dict:
        """
        종목의 거래량 지표 분석

        Args:
            stock_code: 종목 코드
            days: 분석 기간 (기본 60일)

        Returns:
            {
                'code': 종목 코드,
                'avg_volume_20d': 20일 평균 거래량,
                'avg_volume_60d': 60일 평균 거래량,
                'avg_amount_20d': 20일 평균 거래대금 (원),
                'avg_amount_60d': 60일 평균 거래대금 (원),
                'volume_trend': 거래량 추세 ('증가'/'유지'/'감소'),
                'volume_change_pct': 거래량 변화율 (%),
                'volume_cv': 거래량 변동계수 (안정성),
                'recent_volume_surge': 최근 거래량 급증 여부,
                'volume_score': 종합 거래량 점수 (0-100),
                'volume_rank': 등급 ('매우높음'/'높음'/'보통'/'낮음')
            }
        """
        df = self.get_price_data(stock_code, days)

        if len(df) < 20:
            return {
                'code': stock_code,
                'error': '데이터 부족',
                'volume_score': 0,
                'volume_rank': '데이터없음'
            }

        # 1. 평균 거래량
        avg_volume_20 = df['volume'].tail(20).mean()
        avg_volume_60 = df['volume'].mean() if len(df) >= 60 else avg_volume_20

        # 2. 평균 거래대금 (거래량 × 종가)
        df['amount'] = df['volume'] * df['close']
        avg_amount_20 = df['amount'].tail(20).mean()
        avg_amount_60 = df['amount'].mean() if len(df) >= 60 else avg_amount_20

        # 3. 거래량 추세 분석
        volume_change_pct = ((avg_volume_20 / avg_volume_60) - 1) * 100 if avg_volume_60 > 0 else 0

        if volume_change_pct > 20:
            volume_trend = "급증"
        elif volume_change_pct > 10:
            volume_trend = "증가"
        elif volume_change_pct > -10:
            volume_trend = "유지"
        else:
            volume_trend = "감소"

        # 4. 거래량 변동성 (변동계수 = 표준편차 / 평균)
        volume_std = df['volume'].tail(20).std()
        volume_cv = volume_std / avg_volume_20 if avg_volume_20 > 0 else 0

        # 5. 최근 거래량 급증 감지 (최근 5일 vs 20일 평균)
        recent_5d_avg = df['volume'].tail(5).mean()
        recent_volume_surge = recent_5d_avg > avg_volume_20 * 1.5

        # 6. 종합 점수 계산
        volume_score = self.calculate_volume_score(
            avg_amount_20,
            volume_change_pct,
            volume_cv,
            recent_volume_surge
        )

        # 7. 등급 부여
        volume_rank = self.get_volume_rank(volume_score)

        return {
            'code': stock_code,
            'avg_volume_20d': int(avg_volume_20),
            'avg_volume_60d': int(avg_volume_60),
            'avg_amount_20d': float(avg_amount_20),
            'avg_amount_60d': float(avg_amount_60),
            'volume_trend': volume_trend,
            'volume_change_pct': round(volume_change_pct, 2),
            'volume_cv': round(volume_cv, 3),
            'recent_volume_surge': recent_volume_surge,
            'volume_score': round(volume_score, 1),
            'volume_rank': volume_rank
        }

    def calculate_volume_score(
        self,
        avg_amount: float,
        change_pct: float,
        cv: float,
        surge: bool
    ) -> float:
        """
        거래량 종합 점수 계산 (0-100)

        Args:
            avg_amount: 평균 거래대금 (원)
            change_pct: 거래량 변화율 (%)
            cv: 변동계수
            surge: 최근 급증 여부

        Returns:
            종합 점수 (0-100)
        """
        score = 0

        # 1. 거래대금 점수 (0-50점) - 가장 중요
        if avg_amount >= 200_000_000_000:  # 2,000억 이상
            score += 50
        elif avg_amount >= 100_000_000_000:  # 1,000억 이상
            score += 45
        elif avg_amount >= 50_000_000_000:  # 500억 이상
            score += 40
        elif avg_amount >= 20_000_000_000:  # 200억 이상
            score += 30
        elif avg_amount >= 10_000_000_000:  # 100억 이상
            score += 20
        else:
            score += 10

        # 2. 거래량 추세 점수 (0-30점)
        if change_pct > 30:
            score += 30
        elif change_pct > 20:
            score += 25
        elif change_pct > 10:
            score += 20
        elif change_pct > 0:
            score += 15
        elif change_pct > -10:
            score += 10
        else:
            score += 5

        # 3. 안정성 점수 (0-10점)
        if cv < 0.3:
            score += 10
        elif cv < 0.5:
            score += 8
        elif cv < 0.8:
            score += 5
        elif cv < 1.0:
            score += 3
        else:
            score += 0

        # 4. 최근 급증 보너스 (0-10점)
        if surge:
            score += 10

        return min(score, 100)

    def get_volume_rank(self, score: float) -> str:
        """점수에 따른 등급 반환"""
        if score >= 80:
            return "매우높음"
        elif score >= 65:
            return "높음"
        elif score >= 50:
            return "보통"
        elif score >= 35:
            return "낮음"
        else:
            return "매우낮음"

    def rank_stocks_by_volume(
        self,
        stock_codes: List[str],
        min_amount: float = 50_000_000_000
    ) -> List[Dict]:
        """
        종목들을 거래량 기준으로 순위화

        Args:
            stock_codes: 종목 코드 리스트
            min_amount: 최소 거래대금 필터 (기본 500억원)

        Returns:
            거래량 순위 리스트 (높은 순)
        """
        results = []

        print(f"\n{'='*80}")
        print(f"거래량 분석 중... (총 {len(stock_codes)}개 종목)")
        print(f"최소 거래대금 기준: {min_amount/1e8:.0f}억원")
        print(f"{'='*80}\n")

        for code in stock_codes:
            try:
                volume_info = self.analyze_volume(code)

                # 에러 체크
                if 'error' in volume_info:
                    print(f"  ⚠️  {code}: {volume_info['error']}")
                    continue

                # 최소 거래대금 필터
                if volume_info['avg_amount_20d'] < min_amount:
                    print(f"  ❌ {code}: 거래대금 부족 ({volume_info['avg_amount_20d']/1e8:.0f}억원)")
                    continue

                results.append(volume_info)

                print(f"  ✓ {code}: {volume_info['avg_amount_20d']/1e8:.0f}억원 "
                      f"({volume_info['volume_rank']}, 점수: {volume_info['volume_score']:.1f})")

            except Exception as e:
                print(f"  ❌ {code}: 분석 실패 - {str(e)}")
                continue

        # 거래량 점수로 정렬
        results.sort(key=lambda x: x['volume_score'], reverse=True)

        # 순위 부여
        for i, item in enumerate(results):
            item['rank'] = i + 1

        print(f"\n총 {len(results)}개 종목이 기준을 통과했습니다.\n")

        return results

    def get_top_volume_stocks(
        self,
        market: str = "KOSPI",
        limit: int = 20,
        min_amount: float = 50_000_000_000
    ) -> List[Dict]:
        """
        시장에서 거래량 상위 종목 조회

        Args:
            market: 시장 (KOSPI/KOSDAQ)
            limit: 조회 개수
            min_amount: 최소 거래대금

        Returns:
            거래량 상위 종목 리스트
        """
        conn = self.get_db_connection()

        # 시장별 종목 코드 조회
        query = """
            SELECT DISTINCT code
            FROM stocks
            WHERE market = %s
            LIMIT %s
        """

        df = pd.read_sql_query(query, conn, params=(market, limit * 2))
        stock_codes = df['code'].tolist()

        # 거래량 분석 및 순위화
        return self.rank_stocks_by_volume(stock_codes, min_amount)

    def __del__(self):
        """연결 종료"""
        if self.conn and not self.conn.closed:
            self.conn.close()


# 테스트 코드
if __name__ == "__main__":
    analyzer = VolumeAnalyzer()

    # 삼성전자 거래량 분석
    result = analyzer.analyze_volume("005930")

    print("\n삼성전자 거래량 분석 결과:")
    print(f"20일 평균 거래대금: {result['avg_amount_20d']/1e8:.0f}억원")
    print(f"거래량 추세: {result['volume_trend']} ({result['volume_change_pct']:+.1f}%)")
    print(f"안정성(CV): {result['volume_cv']:.3f}")
    print(f"종합 점수: {result['volume_score']:.1f}점 ({result['volume_rank']})")
