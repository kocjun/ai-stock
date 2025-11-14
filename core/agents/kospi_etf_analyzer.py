"""
코스피 지수 ETF 분석 및 예측 모듈

시장 뉴스 기반으로 코스피 지수 방향성을 예측하고
주요 지수 ETF(TIGER 200, KODEX 100 등)의 추천 액션을 제시하는 모듈
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Tuple

# 프로젝트 루트 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# .env 파일 로드
try:
    from dotenv import load_dotenv
    env_file = project_root / ".env"
    if env_file.exists():
        load_dotenv(env_file)
except ImportError:
    pass


class KOSPIETFAnalyzer:
    """코스피 지수 및 ETF 분석 클래스"""

    # 주요 지수 ETF 정보
    KOSPI_ETFS = {
        "TIGER 200": {
            "ticker": "069500",
            "description": "KOSPI 200 지수 연동",
            "expense_ratio": 0.08,
            "category": "대형주",
            "volatility": "중간",
        },
        "KODEX 100": {
            "ticker": "096690",
            "description": "KOSPI 100 대형주",
            "expense_ratio": 0.10,
            "category": "대형주",
            "volatility": "낮음",
        },
        "TIGER 중형주": {
            "ticker": "139290",
            "description": "KOSPI 중형주",
            "expense_ratio": 0.20,
            "category": "중형주",
            "volatility": "높음",
        },
        "KODEX 소형주": {
            "ticker": "139290",
            "description": "KOSPI 소형주",
            "expense_ratio": 0.25,
            "category": "소형주",
            "volatility": "매우높음",
        },
        "TIGER 배당성장": {
            "ticker": "261120",
            "description": "배당주 중심",
            "expense_ratio": 0.15,
            "category": "배당주",
            "volatility": "낮음",
        },
    }

    # 시장 영향 요인
    MARKET_FACTORS = {
        "positive": {
            "반도체_호재": 2.5,
            "수출주_환율이익": 2.0,
            "금융주_금리": 1.5,
            "방위사업주": 1.5,
            "S&P신고가": 1.0,
        },
        "negative": {
            "Fed_금리인상": -2.5,
            "미중_갈등심화": -2.5,
            "한반도_긴장": -2.0,
            "금리인상": -2.0,
            "환율_약세우려": -1.0,
        },
    }

    def __init__(self):
        """초기화"""
        self.timestamp = datetime.now()
        self.market_score = 0
        self.direction = "중립"
        self.etf_recommendations = {}

    def analyze_market_news(self, news_data: Dict[str, List[Dict]]) -> Dict[str, Any]:
        """
        뉴스 데이터 기반 시장 분석

        Args:
            news_data: 뉴스 카테고리별 데이터

        Returns:
            시장 분석 결과
        """
        market_score = 0
        news_analysis = {
            "positive": [],
            "negative": [],
            "neutral": [],
        }

        # 글로벌 시장 분석
        global_news = news_data.get("global", [])
        for news in global_news:
            if "신고가" in news.get("title", ""):
                market_score += self.MARKET_FACTORS["positive"]["S&P신고가"]
                news_analysis["positive"].append(news["title"])
            if "금리 인상" in news.get("title", ""):
                market_score -= self.MARKET_FACTORS["negative"]["Fed_금리인상"]
                news_analysis["negative"].append(news["title"])

        # 반도체 뉴스 분석
        semi_news = news_data.get("semiconductor", [])
        for news in semi_news:
            if "호황" in news.get("description", "") or "진전" in news.get("title", ""):
                market_score += self.MARKET_FACTORS["positive"]["반도체_호재"]
                news_analysis["positive"].append(news["title"])

        # 지정학 분석
        geo_news = news_data.get("geopolitical", [])
        for news in geo_news:
            risk = news.get("risk_level", "")
            if risk == "critical":
                market_score -= self.MARKET_FACTORS["negative"]["미중_갈등심화"]
                news_analysis["negative"].append(news["title"])
            elif risk == "warning":
                market_score -= 1.5
                news_analysis["negative"].append(news["title"])

        # 국내 뉴스 분석
        korea_news = news_data.get("korea", [])
        for news in korea_news:
            if "환율" in news.get("title", "") and "상승" in news.get("title", ""):
                market_score += self.MARKET_FACTORS["positive"]["수출주_환율이익"]
                news_analysis["positive"].append(news["title"])
            if "금리" in news.get("title", "") and "인상" in news.get("title", ""):
                market_score -= self.MARKET_FACTORS["negative"]["금리인상"]
                news_analysis["negative"].append(news["title"])

        self.market_score = market_score
        self._determine_direction()

        return {
            "timestamp": self.timestamp.isoformat(),
            "market_score": market_score,
            "direction": self.direction,
            "news_analysis": news_analysis,
            "summary": self._generate_summary(),
        }

    def _determine_direction(self) -> None:
        """시장 방향성 결정"""
        if self.market_score > 3:
            self.direction = "강세 ⬆️"
        elif self.market_score > 1:
            self.direction = "약세 상승 ↗️"
        elif self.market_score > -1:
            self.direction = "중립 ➡️"
        elif self.market_score > -3:
            self.direction = "약세 하락 ↘️"
        else:
            self.direction = "강세 하락 ⬇️"

    def predict_etf_performance(self) -> Dict[str, Dict[str, Any]]:
        """
        시장 방향성 기반 ETF 성과 예측

        Returns:
            ETF별 예측 결과
        """
        predictions = {}

        for etf_name, etf_info in self.KOSPI_ETFS.items():
            # 변동성에 따른 상승률 조정
            if self.direction == "강세 ⬆️":
                if etf_info["volatility"] == "매우높음":
                    expected_return = self.market_score * 1.3  # 소형주 더 오름
                elif etf_info["volatility"] == "높음":
                    expected_return = self.market_score * 1.15
                elif etf_info["volatility"] == "낮음":
                    expected_return = self.market_score * 0.8
                else:
                    expected_return = self.market_score
            elif self.direction == "강세 하락 ⬇️":
                if etf_info["volatility"] == "매우높음":
                    expected_return = self.market_score * 1.3  # 소형주 더 내림
                elif etf_info["volatility"] == "높음":
                    expected_return = self.market_score * 1.15
                elif etf_info["volatility"] == "낮음":
                    expected_return = self.market_score * 0.8
                else:
                    expected_return = self.market_score
            else:
                expected_return = self.market_score * 0.5

            # 추천 액션 결정
            if expected_return > 2:
                action = "매수 강추"
                action_emoji = "🟢"
            elif expected_return > 0.5:
                action = "매수"
                action_emoji = "🟢"
            elif expected_return > -0.5:
                action = "중립/보유"
                action_emoji = "🟡"
            elif expected_return > -2:
                action = "매도"
                action_emoji = "🔴"
            else:
                action = "매도 강추"
                action_emoji = "🔴"

            predictions[etf_name] = {
                "ticker": etf_info["ticker"],
                "category": etf_info["category"],
                "description": etf_info["description"],
                "expected_return": round(expected_return, 2),
                "expected_return_pct": f"{round(expected_return * 0.5, 1)}%",  # 보수적 추정
                "action": action,
                "action_emoji": action_emoji,
                "reasoning": self._get_reasoning(etf_name, expected_return),
                "risk_level": etf_info["volatility"],
                "expense_ratio": f"{etf_info['expense_ratio']}%",
            }

        self.etf_recommendations = predictions
        return predictions

    def _get_reasoning(self, etf_name: str, expected_return: float) -> str:
        """ETF 추천 근거 생성"""
        etf_info = self.KOSPI_ETFS[etf_name]

        if self.direction == "강세 ⬆️":
            if etf_info["volatility"] == "매우높음":
                return "시장 상승 시 소형주 수익률이 높으므로 적극 추천"
            elif etf_info["category"] == "배당주":
                return "시장 상승장에서 안정적 수익 추구"
            else:
                return "코스피 상승 신호로 지수 연동 ETF 추천"
        elif self.direction == "강세 하락 ⬇️":
            if etf_info["volatility"] == "낮음":
                return "하락장에서 변동성 낮은 제품으로 손실 최소화"
            elif etf_info["category"] == "배당주":
                return "배당 수익으로 손실 일부 보완"
            else:
                return "하락 신호로 신중한 진입 권고"
        else:
            return "시장 중립 구간으로 매수 타이밍 재검토 필요"

    def generate_report(self) -> str:
        """최종 분석 리포트 생성"""
        report = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                      📈 코스피 지수 ETF 분석 보고서                           ║
╚══════════════════════════════════════════════════════════════════════════════╝

📊 분석 시간: {self.timestamp.strftime('%Y년 %m월 %d일 %H:%M')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 시장 방향성 분석
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

시장 점수: {self.market_score:+.1f}점
예상 방향: {self.direction}

분석:
- 긍정 신호: {len(self._get_analysis_summary()['positive'])}개 소식
- 부정 신호: {len(self._get_analysis_summary()['negative'])}개 소식
- 중립 신호: {len(self._get_analysis_summary()['neutral'])}개 소식

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💰 주요 지수 ETF 추천 순위
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

        # 예상 수익률로 정렬
        sorted_etfs = sorted(
            self.etf_recommendations.items(),
            key=lambda x: x[1]["expected_return"],
            reverse=True,
        )

        for idx, (etf_name, rec) in enumerate(sorted_etfs, 1):
            report += f"""
{idx}. {rec['action_emoji']} {etf_name} ({rec['ticker']})
   카테고리: {rec['category']} | 변동성: {rec['risk_level']}
   예상 수익률: {rec['expected_return_pct']}
   추천 액션: {rec['action']}
   근거: {rec['reasoning']}
   수수료: {rec['expense_ratio']}
"""

        report += """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 투자 전략
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

        if "강세" in self.direction and "⬆️" in self.direction:
            report += """
✅ 상승장 전략:
   1. 소형주 ETF로 높은 수익 추구
   2. 중형주 ETF로 적극적 진입
   3. 배당주 ETF로 수익 고착
   4. 분할 매수로 리스크 분산
"""
        elif "강세" in self.direction and "⬇️" in self.direction:
            report += """
⚠️ 하락장 전략:
   1. 안정주/배당주 ETF로 손실 최소화
   2. 변동성 높은 제품 회피
   3. 현금 보유로 진입 기회 대기
   4. 추가 하락 신호 모니터링
"""
        else:
            report += """
🟡 중립장 전략:
   1. 기존 포지션 유지
   2. 추세 확인 후 진입
   3. 충분한 분석 후 신규 진입
   4. 주간 리밸런싱 고려
"""

        report += """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ 주의사항
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

• 본 분석은 뉴스 데이터 기반의 예측이며 절대적 지표가 아닙니다
• 실제 투자 결정 전 개인 재무 상담가와 상담하세요
• 포트폴리오의 20% 이상을 단일 ETF에 집중하지 마세요
• 정기적인 리밸런싱과 손절매 계획을 수립하세요
• 지정학적 리스크 및 금리 정책 변화를 주시하세요

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

        return report

    def _get_analysis_summary(self) -> Dict[str, List[str]]:
        """분석 요약 반환"""
        if hasattr(self, "_analysis_data"):
            return self._analysis_data
        return {"positive": [], "negative": [], "neutral": []}

    def _generate_summary(self) -> str:
        """한 줄 요약"""
        if self.market_score > 3:
            return "강한 상승 신호: 공격적 매수 타이밍"
        elif self.market_score > 1:
            return "약한 상승 신호: 선별적 매수"
        elif self.market_score > -1:
            return "중립: 추세 확인 후 진입"
        elif self.market_score > -3:
            return "약한 하락 신호: 방어적 포지셀닝"
        else:
            return "강한 하락 신호: 현금 보유 및 기회 대기"


def analyze_kospi(news_data: Dict[str, List[Dict]]) -> Tuple[Dict, str]:
    """
    코스피 분석 실행

    Args:
        news_data: 뉴스 카테고리별 데이터

    Returns:
        (분석 결과, 리포트)
    """
    analyzer = KOSPIETFAnalyzer()

    # 분석 실행
    market_analysis = analyzer.analyze_market_news(news_data)

    # ETF 예측
    etf_predictions = analyzer.predict_etf_performance()

    # 리포트 생성
    report = analyzer.generate_report()

    return (
        {
            "market_analysis": market_analysis,
            "etf_predictions": etf_predictions,
        },
        report,
    )


if __name__ == "__main__":
    # 테스트용 샘플 데이터
    sample_data = {
        "global": [
            {
                "title": "S&P 500 신고가 경신",
                "description": "미국 경제 강세",
            },
        ],
        "semiconductor": [
            {
                "title": "Samsung 3nm 공정 진전",
                "description": "반도체 경기 회복 호황",
            },
        ],
        "geopolitical": [
            {
                "title": "미중 기술 갈등 심화",
                "risk_level": "critical",
            },
        ],
        "korea": [
            {
                "title": "원/달러 환율 상승",
                "description": "수출주 호재",
            },
        ],
    }

    result, report = analyze_kospi(sample_data)
    print(report)
    print("\n🔗 결과 데이터:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
