"""
백테스팅 도구 (CrewAI Tool)

과거 데이터 기반 투자 전략 검증 도구
"""

from crewai.tools import BaseTool
from typing import Any
import sys
import os

# 상위 디렉터리 모듈 import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backtesting import run_backtest, compare_strategies, generate_backtest_report
from datetime import datetime, timedelta


class BacktestingTool(BaseTool):
    name: str = "backtesting_tool"
    description: str = """
    과거 데이터 기반 투자 전략 백테스팅 도구

    사용법:
    1. backtest:[전략명],[시작일],[종료일],[종목수]
       - 단일 전략 백테스트 실행
       - 전략명: equal_weight, market_cap, risk_parity
       - 예시: backtest:equal_weight,2024-01-01,2024-12-31,10

    2. compare:[시작일],[종료일],[종목수]
       - 여러 전략 비교 (동일가중, 시총가중, 리스크패리티)
       - 예시: compare:2024-01-01,2024-12-31,10

    3. quick:[종목수]
       - 최근 3개월 빠른 백테스트 (동일가중 전략)
       - 예시: quick:10

    반환: 백테스트 결과 요약 (수익률, Sharpe Ratio, MDD 등)
    """

    def _run(self, command: str) -> str:
        """
        백테스트 실행

        Args:
            command: 명령어 문자열

        Returns:
            백테스트 결과 텍스트
        """
        try:
            parts = command.strip().split(':')
            if len(parts) < 2:
                return "❌ 잘못된 명령어 형식입니다. 사용법을 확인하세요."

            cmd_type = parts[0].lower()
            args = parts[1].split(',')

            # 1. 단일 전략 백테스트
            if cmd_type == "backtest":
                if len(args) < 4:
                    return "❌ 형식: backtest:[전략명],[시작일],[종료일],[종목수]"

                strategy = args[0].strip()
                start_date = args[1].strip()
                end_date = args[2].strip()
                top_n = int(args[3].strip())

                # 백테스트 실행
                result = run_backtest(
                    start_date=start_date,
                    end_date=end_date,
                    strategy=strategy,
                    top_n=top_n
                )

                if result['status'] != 'success':
                    return f"❌ 백테스트 실패: {result.get('message', '알 수 없는 오류')}"

                # 리포트 생성
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                report_file = f"reports/backtest_{strategy}_{timestamp}.md"

                # reports 디렉터리 생성
                os.makedirs("reports", exist_ok=True)

                generate_backtest_report(result, report_file)

                # 결과 요약
                summary = f"""
✅ 백테스트 완료

전략: {strategy}
기간: {start_date} ~ {end_date} ({result['period']['years']}년)
종목수: {top_n}개

📊 성과 지표:
• 총 수익률: {result['returns']['total_return']:+.2f}%
• CAGR: {result['returns']['cagr']:+.2f}%
• 변동성: {result['returns']['volatility']:.2f}%
• Sharpe Ratio: {result['returns']['sharpe_ratio']:.2f}
• Sortino Ratio: {result['returns']['sortino_ratio']:.2f}
• MDD: {result['returns']['max_drawdown']:.2f}%
• 승률: {result['returns']['win_rate']:.2f}%

📈 벤치마크 비교 (KOSPI):
• KOSPI 수익률: {result['benchmark']['total_return']:+.2f}%
• 알파 (초과수익): {result['benchmark']['alpha']:+.2f}%p
• 베타: {result['benchmark']['beta']:.2f}

📁 상세 리포트: {report_file}
"""
                return summary.strip()

            # 2. 전략 비교
            elif cmd_type == "compare":
                if len(args) < 3:
                    return "❌ 형식: compare:[시작일],[종료일],[종목수]"

                start_date = args[0].strip()
                end_date = args[1].strip()
                top_n = int(args[2].strip())

                # 전략 비교 실행
                result = compare_strategies(
                    start_date=start_date,
                    end_date=end_date,
                    top_n=top_n
                )

                if result['status'] != 'success':
                    return "❌ 전략 비교 실패"

                # 결과 요약
                summary = f"""
✅ 전략 비교 완료

기간: {start_date} ~ {end_date}
종목수: {top_n}개

📊 전략별 성과:

"""
                # 전략별 결과 테이블
                for strategy, metrics in result['strategies'].items():
                    summary += f"""
▶ {strategy.upper()}
  - 총 수익률: {metrics['total_return']:+.2f}%
  - CAGR: {metrics['cagr']:+.2f}%
  - 변동성: {metrics['volatility']:.2f}%
  - Sharpe Ratio: {metrics['sharpe_ratio']:.2f}
  - MDD: {metrics['max_drawdown']:.2f}%
  - 알파: {metrics['alpha']:+.2f}%p
"""

                # 최고 성과 전략
                if result['best_strategy']:
                    summary += f"""
🏆 최고 성과 전략: {result['best_strategy'].upper()}
   (Sharpe Ratio 기준)
"""

                return summary.strip()

            # 3. 빠른 백테스트 (최근 3개월)
            elif cmd_type == "quick":
                if len(args) < 1:
                    return "❌ 형식: quick:[종목수]"

                top_n = int(args[0].strip())

                # 날짜 계산
                end_date = datetime.now().strftime('%Y-%m-%d')
                start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')

                # 백테스트 실행
                result = run_backtest(
                    start_date=start_date,
                    end_date=end_date,
                    strategy="equal_weight",
                    top_n=top_n
                )

                if result['status'] != 'success':
                    return f"❌ 백테스트 실패: {result.get('message', '알 수 없는 오류')}"

                # 결과 요약
                summary = f"""
✅ 빠른 백테스트 완료 (최근 3개월)

전략: 동일가중 (Equal Weight)
기간: {start_date} ~ {end_date}
종목수: {top_n}개

📊 주요 지표:
• 총 수익률: {result['returns']['total_return']:+.2f}%
• Sharpe Ratio: {result['returns']['sharpe_ratio']:.2f}
• MDD: {result['returns']['max_drawdown']:.2f}%
• KOSPI 대비 알파: {result['benchmark']['alpha']:+.2f}%p
"""
                return summary.strip()

            else:
                return f"❌ 알 수 없는 명령어: {cmd_type}"

        except ValueError as e:
            return f"❌ 잘못된 입력값: {str(e)}"
        except Exception as e:
            return f"❌ 백테스트 실행 중 오류: {str(e)}"


if __name__ == "__main__":
    """도구 테스트"""
    print("BacktestingTool 테스트\n")

    tool = BacktestingTool()

    # 테스트 1: 빠른 백테스트
    print("테스트 1: 빠른 백테스트 (최근 3개월)")
    print("-" * 60)
    result = tool.run("quick:10")
    print(result)

    print("\n" + "="*60 + "\n")

    # 테스트 2: 단일 전략 백테스트
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')

    print("테스트 2: 6개월 백테스트 (동일가중)")
    print("-" * 60)
    result = tool.run(f"backtest:equal_weight,{start_date},{end_date},10")
    print(result)
