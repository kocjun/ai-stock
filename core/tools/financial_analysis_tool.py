"""
재무 분석 도구 (CrewAI Tool)

재무 지표 계산 및 팩터 스코어링 기능을 CrewAI 에이전트에서 사용할 수 있도록 래핑합니다.
"""

from crewai.tools import BaseTool
from typing import Any, Optional
import sys
import os

# 상위 디렉터리 모듈 import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.modules.financial_metrics import analyze_stock_fundamentals
from core.modules.factor_scoring import screen_stocks, format_screening_result


class FinancialAnalysisTool(BaseTool):
    name: str = "financial_analysis"
    description: str = """
    재무 분석 도구

    특정 종목의 재무 지표를 분석하거나 전체 종목을 스크리닝합니다.

    사용법:
    - 종목 분석: "analyze:005930" (종목 코드 지정)
    - 전체 스크리닝: "screen:20" (상위 N개 종목)
    - 필터링 스크리닝: "screen:20,roe=10,debt=150" (ROE 10% 이상, 부채비율 150% 이하)

    예시:
    - "analyze:005930" → 삼성전자 재무 분석
    - "screen:20" → 상위 20개 종목 스크리닝
    - "screen:30,roe=15,debt=100" → ROE 15% 이상, 부채비율 100% 이하 종목 중 상위 30개
    """

    def _run(self, command: str) -> str:
        """
        재무 분석 실행

        Args:
            command: 명령어 문자열

        Returns:
            분석 결과 문자열
        """
        try:
            # 명령어 파싱
            if command.startswith("analyze:"):
                stock_code = command.split(":", 1)[1].strip()
                return self._analyze_stock(stock_code)

            elif command.startswith("screen:"):
                params = command.split(":", 1)[1].strip()
                return self._screen_stocks(params)

            else:
                return "❌ 잘못된 명령어 형식입니다. 'analyze:종목코드' 또는 'screen:개수' 형식으로 입력하세요."

        except Exception as e:
            return f"❌ 재무 분석 실패: {str(e)}"

    def _analyze_stock(self, stock_code: str) -> str:
        """
        특정 종목 재무 분석

        Args:
            stock_code: 종목 코드

        Returns:
            분석 결과 문자열
        """
        result = analyze_stock_fundamentals(stock_code)

        if result['status'] == 'no_data':
            return f"❌ {stock_code}: {result['message']}"

        # 결과 포맷팅
        output = []
        output.append("=" * 60)
        output.append(f"📊 재무 분석: {result['name']} ({result['code']})")
        output.append("=" * 60)
        output.append(f"섹터: {result['sector']}")
        output.append(f"기준: {result['year']}년 {result['quarter']}분기")
        output.append("")
        output.append("📈 재무 데이터:")
        output.append(f"  매출: {result['revenue']:,}원")
        output.append(f"  영업이익: {result['operating_profit']:,}원")
        output.append(f"  순이익: {result['net_profit']:,}원")
        output.append("")
        output.append("💰 수익성 지표:")
        output.append(f"  ROE: {result['roe']}%")
        output.append(f"  ROA: {result['roa']}%")
        output.append(f"  영업이익률: {result['operating_margin']}%")
        output.append(f"  순이익률: {result['net_margin']}%")
        output.append("")
        output.append("📊 안정성 지표:")
        output.append(f"  부채비율: {result['debt_ratio']}%")
        output.append("")

        if result['revenue_growth'] is not None:
            output.append("📈 성장률 (YoY):")
            output.append(f"  매출 성장률: {result['revenue_growth']}%")
            output.append(f"  이익 성장률: {result['profit_growth']}%")
            output.append("")

        output.append("✅ 분석 완료")

        return "\n".join(output)

    def _screen_stocks(self, params: str) -> str:
        """
        종목 스크리닝

        Args:
            params: 파라미터 문자열 (예: "20" 또는 "20,roe=10,debt=150")

        Returns:
            스크리닝 결과 문자열
        """
        # 파라미터 파싱
        parts = params.split(",")
        top_n = int(parts[0].strip())

        min_roe = 0
        max_debt_ratio = 200

        for part in parts[1:]:
            if "=" in part:
                key, value = part.split("=")
                key = key.strip().lower()
                value = float(value.strip())

                if key == "roe":
                    min_roe = value
                elif key == "debt":
                    max_debt_ratio = value

        # 스크리닝 실행
        print(f"🔍 스크리닝 조건: 상위 {top_n}개, ROE >= {min_roe}%, 부채비율 <= {max_debt_ratio}%")

        result_df = screen_stocks(
            top_n=top_n,
            min_roe=min_roe,
            max_debt_ratio=max_debt_ratio
        )

        if result_df.empty:
            return "❌ 스크리닝 결과가 없습니다. 조건을 완화하거나 재무 데이터를 먼저 수집하세요."

        # 결과 포맷팅
        return format_screening_result(result_df)


class FactorWeightTool(BaseTool):
    name: str = "factor_weight_config"
    description: str = """
    팩터 가중치 설정 도구

    스크리닝 시 각 팩터의 가중치를 조정합니다.

    사용법:
    - "show" → 현재 가중치 표시
    - "set:value=0.3,growth=0.3,profitability=0.2,momentum=0.1,stability=0.1" → 가중치 설정

    주의: 가중치 합은 1.0이어야 합니다.
    """

    # 클래스 변수로 가중치 저장 (세션 간 유지)
    weights: dict = {
        'value': 0.25,
        'growth': 0.25,
        'profitability': 0.25,
        'momentum': 0.15,
        'stability': 0.1
    }

    def _run(self, command: str) -> str:
        """
        가중치 설정/조회

        Args:
            command: 명령어 문자열

        Returns:
            결과 문자열
        """
        try:
            if command.strip().lower() == "show":
                return self._show_weights()

            elif command.startswith("set:"):
                params = command.split(":", 1)[1].strip()
                return self._set_weights(params)

            else:
                return "❌ 잘못된 명령어입니다. 'show' 또는 'set:...' 형식으로 입력하세요."

        except Exception as e:
            return f"❌ 가중치 설정 실패: {str(e)}"

    def _show_weights(self) -> str:
        """현재 가중치 표시"""
        output = []
        output.append("=" * 50)
        output.append("⚖️  팩터 가중치 설정")
        output.append("=" * 50)

        for factor, weight in self.weights.items():
            output.append(f"  {factor:15s}: {weight:.2f} ({weight*100:.0f}%)")

        output.append("")
        output.append(f"  합계: {sum(self.weights.values()):.2f}")

        return "\n".join(output)

    def _set_weights(self, params: str) -> str:
        """
        가중치 설정

        Args:
            params: "value=0.3,growth=0.3,..." 형식

        Returns:
            결과 문자열
        """
        new_weights = {}

        # 파라미터 파싱
        for part in params.split(","):
            if "=" in part:
                key, value = part.split("=")
                key = key.strip().lower()
                value = float(value.strip())

                if key in ['value', 'growth', 'profitability', 'momentum', 'stability']:
                    new_weights[key] = value
                else:
                    return f"❌ 알 수 없는 팩터: {key}"

        # 가중치 합 검증
        total = sum(new_weights.values())
        if abs(total - 1.0) > 0.01:
            return f"❌ 가중치 합이 1.0이 아닙니다: {total:.2f}"

        # 기존 가중치와 병합
        self.weights.update(new_weights)

        return f"✅ 가중치 업데이트 완료\n\n{self._show_weights()}"


if __name__ == '__main__':
    """테스트 코드"""
    print("=== 재무 분석 도구 테스트 ===\n")

    tool = FinancialAnalysisTool()

    # 테스트 1: 종목 분석
    print("1. 종목 분석 테스트")
    print("-" * 60)
    result = tool.run("analyze:005930")
    print(result)
    print("\n")

    # 테스트 2: 스크리닝
    print("2. 스크리닝 테스트")
    print("-" * 60)
    result = tool.run("screen:5")
    print(result)
    print("\n")

    # 테스트 3: 가중치 도구
    print("3. 가중치 도구 테스트")
    print("-" * 60)
    weight_tool = FactorWeightTool()
    print(weight_tool.run("show"))
    print("\n")

    print("✅ 재무 분석 도구 테스트 완료!")
