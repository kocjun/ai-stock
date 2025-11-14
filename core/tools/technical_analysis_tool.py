"""
기술적 분석 도구 (CrewAI Tool)

기술적 지표 계산 기능을 CrewAI 에이전트에서 사용할 수 있도록 래핑합니다.
"""

from crewai.tools import BaseTool
from typing import Any, Optional
import sys
import os

# 상위 디렉터리 모듈 import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.modules.technical_indicators import analyze_technical_indicators, get_technical_signals


class TechnicalAnalysisTool(BaseTool):
    name: str = "technical_analysis"
    description: str = """
    기술적 분석 도구

    가격 데이터를 기반으로 기술적 지표를 계산하고 매매 시그널을 분석합니다.

    사용법:
    - 단일 종목 분석: "analyze:005930" 또는 "analyze:005930,120" (종목코드, 분석기간)
    - 여러 종목 시그널: "signals:005930,000660,035420" (종목코드 나열)

    지표:
    - 이동평균 (SMA, EMA)
    - RSI (과매수/과매도)
    - MACD (매매 시그널)
    - 볼린저 밴드
    - 변동성

    예시:
    - "analyze:005930" → 삼성전자 기술적 분석 (120일)
    - "analyze:000660,60" → SK하이닉스 기술적 분석 (60일)
    - "signals:005930,000660,035420" → 3개 종목 시그널 조회
    """

    def _run(self, command: str) -> str:
        """
        기술적 분석 실행

        Args:
            command: 명령어 문자열

        Returns:
            분석 결과 문자열
        """
        try:
            # 명령어 파싱
            if command.startswith("analyze:"):
                params = command.split(":", 1)[1].strip()
                return self._analyze_stock(params)

            elif command.startswith("signals:"):
                params = command.split(":", 1)[1].strip()
                return self._get_signals(params)

            else:
                return "❌ 잘못된 명령어 형식입니다. 'analyze:종목코드' 또는 'signals:종목코드들' 형식으로 입력하세요."

        except Exception as e:
            return f"❌ 기술적 분석 실패: {str(e)}"

    def _analyze_stock(self, params: str) -> str:
        """
        특정 종목 기술적 분석

        Args:
            params: "종목코드" 또는 "종목코드,기간"

        Returns:
            분석 결과 문자열
        """
        parts = params.split(",")
        stock_code = parts[0].strip()
        days = int(parts[1].strip()) if len(parts) > 1 else 120

        result = analyze_technical_indicators(stock_code, days)

        if result['status'] == 'no_data':
            return f"❌ {stock_code}: {result['message']}"

        # 결과 포맷팅
        output = []
        output.append("=" * 70)
        output.append(f"📈 기술적 분석: {result['code']}")
        output.append("=" * 70)
        output.append(f"기준일: {result['date']}")
        output.append(f"종가: {result['close']:,.0f}원")
        output.append("")

        output.append("📊 이동평균:")
        output.append(f"  SMA(20): {result['sma_20']:,.0f}원" if result['sma_20'] else "  SMA(20): N/A")
        output.append(f"  SMA(60): {result['sma_60']:,.0f}원" if result['sma_60'] else "  SMA(60): N/A")
        output.append(f"  EMA(20): {result['ema_20']:,.0f}원" if result['ema_20'] else "  EMA(20): N/A")

        # 이동평균 위치
        if result['sma_20'] and result['sma_60']:
            if result['close'] > result['sma_20'] > result['sma_60']:
                output.append("  → 상승 추세 (종가 > SMA20 > SMA60)")
            elif result['close'] < result['sma_20'] < result['sma_60']:
                output.append("  → 하락 추세 (종가 < SMA20 < SMA60)")
            else:
                output.append("  → 박스권")

        output.append("")

        output.append("🔄 모멘텀 지표:")
        if result['rsi'] is not None:
            rsi_status = ""
            if result['rsi'] < 30:
                rsi_status = " (과매도)"
            elif result['rsi'] > 70:
                rsi_status = " (과매수)"
            output.append(f"  RSI(14): {result['rsi']:.2f}{rsi_status}")

        if result['macd'] is not None:
            macd_signal = "매수" if result['macd'] > result['macd_signal'] else "매도"
            output.append(f"  MACD: {result['macd']:.4f}")
            output.append(f"  Signal: {result['macd_signal']:.4f}")
            output.append(f"  Histogram: {result['macd_histogram']:.4f} → {macd_signal} 신호")

        output.append("")

        output.append("📏 볼린저 밴드:")
        if result['bb_upper'] and result['bb_lower']:
            output.append(f"  상단: {result['bb_upper']:,.0f}원")
            output.append(f"  중간: {result['bb_middle']:,.0f}원")
            output.append(f"  하단: {result['bb_lower']:,.0f}원")

            # 밴드 내 위치
            band_width = result['bb_upper'] - result['bb_lower']
            position = (result['close'] - result['bb_lower']) / band_width * 100
            output.append(f"  현재 위치: {position:.1f}% (하단 0% ~ 상단 100%)")

            if result['close'] > result['bb_upper']:
                output.append("  → 상단 돌파 (과열)")
            elif result['close'] < result['bb_lower']:
                output.append("  → 하단 이탈 (침체)")

        output.append("")

        output.append("📉 변동성:")
        if result['volatility'] is not None:
            vol_level = ""
            if result['volatility'] < 20:
                vol_level = " (낮음)"
            elif result['volatility'] > 40:
                vol_level = " (높음)"
            output.append(f"  연율화 변동성: {result['volatility']:.2f}%{vol_level}")

        output.append("")

        if result['signals']:
            output.append("🚨 주요 시그널:")
            for signal in result['signals']:
                output.append(f"  • {signal}")
        else:
            output.append("🚨 주요 시그널: 없음")

        output.append("")
        output.append("✅ 분석 완료")

        return "\n".join(output)

    def _get_signals(self, params: str) -> str:
        """
        여러 종목의 기술적 시그널 조회

        Args:
            params: "종목코드1,종목코드2,종목코드3,..."

        Returns:
            시그널 요약 문자열
        """
        stock_codes = [code.strip() for code in params.split(",")]

        if not stock_codes:
            return "❌ 종목 코드를 입력하세요."

        signals_df = get_technical_signals(stock_codes, days=120)

        if signals_df.empty:
            return "❌ 시그널 조회 실패 또는 데이터 없음"

        # 결과 포맷팅
        output = []
        output.append("=" * 80)
        output.append(f"📊 기술적 시그널 요약 ({len(signals_df)}개 종목)")
        output.append("=" * 80)
        output.append("")

        for idx, row in signals_df.iterrows():
            output.append(f"[{row['code']}]")
            output.append(f"  RSI: {row['rsi']:.2f} | MACD: {row['macd_signal']} | 추세: {row['trend']} | 변동성: {row['volatility']:.1f}%")
            output.append(f"  시그널: {row['signals']}")
            output.append("")

        output.append("✅ 시그널 조회 완료")

        return "\n".join(output)


if __name__ == '__main__':
    """테스트 코드"""
    print("=== 기술적 분석 도구 테스트 ===\n")

    tool = TechnicalAnalysisTool()

    # 테스트 1: 단일 종목 분석
    print("1. 단일 종목 분석 테스트")
    print("-" * 70)
    result = tool.run("analyze:005930")
    print(result)
    print("\n")

    # 테스트 2: 여러 종목 시그널
    print("2. 여러 종목 시그널 테스트")
    print("-" * 70)
    result = tool.run("signals:005930,000660,035420")
    print(result)
    print("\n")

    print("✅ 기술적 분석 도구 테스트 완료!")
