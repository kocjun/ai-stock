"""
AI 기반 업종별 대장주 자동 선정 시스템

거래량, 재무, 기술적 지표를 종합하여 각 업종의 대장주를 동적으로 선정합니다.
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional
import pandas as pd

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from core.modules.volume_analysis import VolumeAnalyzer
from core.utils.exclusion_manager import filter_excluded_recommendations, is_stock_excluded
from core.utils.db_utils import get_db_connection


# 주요 업종 정의
MAIN_SECTORS = {
    "반도체/전기전자": ["반도체", "전자", "전기전자", "디스플레이"],
    "자동차/운수장비": ["자동차", "자동차부품", "운수장비", "조선"],
    "화학": ["화학", "정유", "플라스틱", "타이어"],
    "금융": ["은행", "증권", "보험", "금융"],
    "IT/인터넷": ["인터넷", "게임", "소프트웨어", "IT서비스", "통신서비스"]
}


class AISectorLeaderSelector:
    """AI 기반 업종별 대장주 선정기"""

    def __init__(self):
        self.volume_analyzer = VolumeAnalyzer()
        self.conn = None

    def get_db_connection(self):
        """DB 연결"""
        if self.conn is None or self.conn.closed:
            self.conn = get_db_connection()
        return self.conn

    def get_stocks_by_sector(self, market: str = "KOSPI", limit: int = 100) -> Dict[str, List[Dict]]:
        """
        시장의 종목을 업종별로 분류

        Args:
            market: 시장 (KOSPI/KOSDAQ)
            limit: 조회 개수

        Returns:
            {
                "반도체/전기전자": [{"code": "005930", "name": "삼성전자", ...}, ...],
                "자동차/운수장비": [...],
                ...
            }
        """
        conn = self.get_db_connection()

        query = """
            SELECT code, name, sector, market
            FROM stocks
            WHERE market = %s
            LIMIT %s
        """

        df = pd.read_sql_query(query, conn, params=(market, limit))

        # 업종별로 그룹핑
        sector_groups = {sector: [] for sector in MAIN_SECTORS.keys()}

        for _, row in df.iterrows():
            stock_sector = row['sector'] or ""

            # 각 메인 섹터의 키워드와 매칭
            matched = False
            for main_sector, keywords in MAIN_SECTORS.items():
                if any(keyword in stock_sector for keyword in keywords):
                    sector_groups[main_sector].append({
                        'code': row['code'],
                        'name': row['name'],
                        'sector': stock_sector,
                        'market': row['market']
                    })
                    matched = True
                    break

            # 매칭되지 않으면 기타로 분류
            if not matched and stock_sector:
                if "기타" not in sector_groups:
                    sector_groups["기타"] = []
                sector_groups["기타"].append({
                    'code': row['code'],
                    'name': row['name'],
                    'sector': stock_sector,
                    'market': row['market']
                })

        # 빈 업종 제거
        sector_groups = {k: v for k, v in sector_groups.items() if len(v) > 0}

        return sector_groups

    def analyze_stock_comprehensive(self, stock_code: str, stock_name: str) -> Optional[Dict]:
        """
        종목에 대한 종합 분석 (거래량 + 재무 + 기술적 + 리스크)

        Returns:
            {
                'code': 종목 코드,
                'name': 종목명,
                'volume_score': 거래량 점수,
                'financial_score': 재무 점수,
                'technical_score': 기술적 점수,
                'risk_score': 리스크 점수,
                'total_score': 종합 점수,
                '상세 정보들...'
            }
        """
        try:
            # 1. 거래량 분석 (가중치: 30%)
            volume_info = self.volume_analyzer.analyze_volume(stock_code)

            if 'error' in volume_info:
                return None

            volume_score = volume_info['volume_score']

            # 2. 재무 분석 (가중치: 30%)
            financial_score = self.analyze_financials(stock_code)

            # 3. 기술적 분석 (가중치: 20%)
            technical_score = self.analyze_technicals(stock_code)

            # 4. 리스크 분석 (가중치: 20%)
            risk_score = self.analyze_risk(stock_code)

            # 5. 종합 점수 계산
            total_score = (
                volume_score * 0.30 +
                financial_score * 0.30 +
                technical_score * 0.20 +
                risk_score * 0.20
            )

            return {
                'code': stock_code,
                'name': stock_name,
                'volume_score': round(volume_score, 1),
                'volume_amount': volume_info['avg_amount_20d'],
                'volume_trend': volume_info['volume_trend'],
                'financial_score': round(financial_score, 1),
                'technical_score': round(technical_score, 1),
                'risk_score': round(risk_score, 1),
                'total_score': round(total_score, 1)
            }

        except Exception as e:
            print(f"  ❌ {stock_code} ({stock_name}) 분석 실패: {str(e)}")
            return None

    def analyze_financials(self, stock_code: str) -> float:
        """
        재무 점수 계산 (0-100)

        간소화 버전: 실제로는 financial_metrics 모듈 활용
        """
        try:
            # TODO: 실제 재무 데이터 조회 및 점수 계산
            # 현재는 기본 점수 반환
            return 70.0
        except:
            return 50.0

    def analyze_technicals(self, stock_code: str) -> float:
        """
        기술적 점수 계산 (0-100)

        간소화 버전: 실제로는 technical_analysis 모듈 활용
        """
        try:
            # TODO: 실제 기술적 분석
            # 현재는 기본 점수 반환
            return 70.0
        except:
            return 50.0

    def analyze_risk(self, stock_code: str) -> float:
        """
        리스크 점수 계산 (0-100, 높을수록 안전)

        간소화 버전: 실제로는 risk_analysis 모듈 활용
        """
        try:
            # TODO: 실제 리스크 분석
            # 현재는 기본 점수 반환
            return 70.0
        except:
            return 50.0

    def select_sector_leaders(
        self,
        market: str = "KOSPI",
        sectors: List[str] = None,
        leaders_per_sector: int = 1,
        min_volume_amount: float = 50_000_000_000
    ) -> List[Dict]:
        """
        AI 기반 업종별 대장주 자동 선정

        Args:
            market: 시장 (KOSPI/KOSDAQ)
            sectors: 대상 업종 리스트 (None이면 전체)
            leaders_per_sector: 업종당 선정 개수
            min_volume_amount: 최소 거래대금 (기본 500억원)

        Returns:
            선정된 대장주 리스트
        """
        print(f"\n{'='*80}")
        print(f"AI 기반 업종별 대장주 자동 선정")
        print(f"{'='*80}\n")
        print(f"시장: {market}")
        print(f"업종당 선정: {leaders_per_sector}개")
        print(f"최소 거래대금: {min_volume_amount/1e8:.0f}억원\n")

        # 1. 업종별 종목 분류
        sector_stocks = self.get_stocks_by_sector(market)

        if sectors:
            # 지정된 업종만 필터링
            sector_stocks = {k: v for k, v in sector_stocks.items() if k in sectors}

        all_leaders = []

        # 2. 각 업종별로 대장주 선정
        for sector_name, stocks in sector_stocks.items():
            print(f"\n[{sector_name}] 분석 중... (총 {len(stocks)}개 종목)")
            print("-" * 80)

            candidates = []

            for stock in stocks:
                # 블랙리스트 체크
                if is_stock_excluded(stock['code']):
                    print(f"  ⚠️  {stock['name']} ({stock['code']}): 블랙리스트 제외")
                    continue

                # 종합 분석
                analysis = self.analyze_stock_comprehensive(stock['code'], stock['name'])

                if analysis is None:
                    continue

                # 최소 거래대금 필터
                if analysis['volume_amount'] < min_volume_amount:
                    print(f"  ❌ {stock['name']}: 거래대금 부족 "
                          f"({analysis['volume_amount']/1e8:.0f}억원)")
                    continue

                analysis['sector'] = sector_name
                candidates.append(analysis)

                print(f"  ✓ {stock['name']}: 종합 {analysis['total_score']:.1f}점 "
                      f"(거래량 {analysis['volume_score']:.1f}, "
                      f"재무 {analysis['financial_score']:.1f}, "
                      f"기술 {analysis['technical_score']:.1f}, "
                      f"리스크 {analysis['risk_score']:.1f})")

            if len(candidates) == 0:
                print(f"  ⚠️  {sector_name}: 기준을 만족하는 종목 없음")
                continue

            # 3. 종합 점수로 정렬
            candidates.sort(key=lambda x: x['total_score'], reverse=True)

            # 4. 상위 N개 선정
            selected = candidates[:leaders_per_sector]

            print(f"\n[{sector_name}] 최종 선정:")
            for i, leader in enumerate(selected):
                print(f"  🥇 {i+1}순위: {leader['name']} ({leader['code']})")
                print(f"     종합 점수: {leader['total_score']:.1f}점")
                print(f"     거래대금: {leader['volume_amount']/1e8:.0f}억원 ({leader['volume_trend']})")
                print(f"     세부: 거래량 {leader['volume_score']:.1f} | "
                      f"재무 {leader['financial_score']:.1f} | "
                      f"기술 {leader['technical_score']:.1f} | "
                      f"리스크 {leader['risk_score']:.1f}")

                # 추천 사유 생성
                leader['reason'] = (
                    f"{sector_name} 대장주 (종합{leader['total_score']:.0f}점) - "
                    f"거래대금 {leader['volume_amount']/1e8:.0f}억원, "
                    f"{leader['volume_trend']} 추세"
                )

            all_leaders.extend(selected)

        # 5. 비중 계산 (동일 가중)
        if all_leaders:
            weight = 1.0 / len(all_leaders)
            for leader in all_leaders:
                leader['weight'] = weight

        print(f"\n{'='*80}")
        print(f"✅ 총 {len(all_leaders)}개 대장주 선정 완료")
        print(f"{'='*80}\n")

        return all_leaders


def get_ai_sector_leader_recommendations(
    market: str = "KOSPI",
    num_sectors: int = 5,
    leaders_per_sector: int = 1,
    min_volume_amount: float = 50_000_000_000
) -> List[Dict]:
    """
    AI 기반 대장주 추천 (외부 호출용)

    Args:
        market: 시장
        num_sectors: 선택할 업종 수
        leaders_per_sector: 업종당 대장주 수
        min_volume_amount: 최소 거래대금

    Returns:
        추천 종목 리스트 (trading_crew.py 포맷과 동일)
    """
    selector = AISectorLeaderSelector()

    # 주요 5개 업종 선택
    main_sectors = list(MAIN_SECTORS.keys())[:num_sectors]

    return selector.select_sector_leaders(
        market=market,
        sectors=main_sectors,
        leaders_per_sector=leaders_per_sector,
        min_volume_amount=min_volume_amount
    )


# 테스트 코드
if __name__ == "__main__":
    print("AI 기반 대장주 선정 시스템 테스트\n")

    # 대장주 선정
    leaders = get_ai_sector_leader_recommendations(
        market="KOSPI",
        num_sectors=5,
        leaders_per_sector=1,
        min_volume_amount=50_000_000_000  # 500억원
    )

    print(f"\n최종 추천 대장주:")
    for leader in leaders:
        print(f"  • {leader['name']} ({leader['code']}): "
              f"{leader['weight']*100:.1f}% - {leader['reason']}")
