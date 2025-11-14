"""
리스크 분석 CrewAI 도구

종목 및 포트폴리오의 리스크 지표를 계산하는 도구
"""

from crewai.tools import BaseTool
from typing import Any
import json
from core.modules.risk_analysis import calculate_risk_score, analyze_portfolio_risk


class RiskAnalysisTool(BaseTool):
    name: str = "risk_analyzer"
    description: str = """
    종목 또는 포트폴리오의 리스크를 분석합니다.

    사용법:
    - 단일 종목 분석: risk <종목코드>
      예: risk 005930

    - 포트폴리오 분석: portfolio <종목코드1>,<종목코드2>,... [비중1,비중2,...]
      예: portfolio 005930,000660,035720 0.4,0.3,0.3
      (비중 생략 시 동일가중)

    출력:
    - 변동성, MDD, VaR, Sharpe Ratio 등 리스크 지표
    - 리스크 점수 (0-10) 및 등급
    - 포트폴리오의 경우 분산 효과 분석
    """

    def _run(self, argument: str) -> str:
        """
        리스크 분석 실행

        Args:
            argument: 명령어 문자열

        Returns:
            분석 결과 (JSON 형식의 문자열)
        """
        try:
            parts = argument.strip().split()

            if len(parts) == 0:
                return json.dumps({
                    'status': 'error',
                    'message': '명령어를 입력하세요. 예: risk 005930 또는 portfolio 005930,000660'
                }, ensure_ascii=False, indent=2)

            command = parts[0].lower()

            # 단일 종목 리스크 분석
            if command == 'risk':
                if len(parts) < 2:
                    return json.dumps({
                        'status': 'error',
                        'message': '종목 코드를 입력하세요. 예: risk 005930'
                    }, ensure_ascii=False, indent=2)

                stock_code = parts[1]
                days = int(parts[2]) if len(parts) > 2 else 252

                result = calculate_risk_score(stock_code, days)

                if result['status'] == 'success':
                    # 분석 결과를 자연어로 변환
                    summary = f"""
✓ [{result['stock_code']}] 리스크 분석 완료 (기간: {result['period_days']}일)

📊 변동성 지표:
- 연간 변동성: {result['volatility']}%
- 하방 편차: {result['downside_deviation']}%

📉 손실 리스크:
- 최대 낙폭(MDD): {result['max_drawdown']}%
  * 고점: {result['peak_date']}
  * 저점: {result['trough_date']}
- VaR(95%): {result['var_95']}% (하루에 최대 이만큼 손실 가능)

📈 수익성 대비 리스크:
- Sharpe Ratio: {result['sharpe_ratio']} (높을수록 좋음)
- Sortino Ratio: {result['sortino_ratio']} (하방 리스크 고려)
- 승률: {result['win_rate']}%

⚠️ 종합 리스크 평가:
- 리스크 점수: {result['risk_score']}/10
- 리스크 등급: {result['risk_grade']}
"""
                    result['summary'] = summary.strip()

                return json.dumps(result, ensure_ascii=False, indent=2)

            # 포트폴리오 리스크 분석
            elif command == 'portfolio':
                if len(parts) < 2:
                    return json.dumps({
                        'status': 'error',
                        'message': '종목 코드를 입력하세요. 예: portfolio 005930,000660,035720'
                    }, ensure_ascii=False, indent=2)

                # 종목 코드 파싱
                stock_codes = parts[1].split(',')

                # 비중 파싱 (옵션)
                weights = None
                if len(parts) > 2:
                    try:
                        weights = [float(w) for w in parts[2].split(',')]
                    except ValueError:
                        return json.dumps({
                            'status': 'error',
                            'message': '비중은 숫자로 입력하세요. 예: 0.4,0.3,0.3'
                        }, ensure_ascii=False, indent=2)

                days = int(parts[3]) if len(parts) > 3 else 252

                result = analyze_portfolio_risk(stock_codes, weights, days)

                if result['status'] == 'success':
                    # 분석 결과를 자연어로 변환
                    summary = f"""
✓ 포트폴리오 리스크 분석 완료

📦 포트폴리오 구성:
- 종목 수: {result['portfolio_size']}개
- 종목: {', '.join(result['stocks'])}
- 비중: {', '.join([f'{w*100:.1f}%' for w in result['weights']])}

📊 포트폴리오 리스크:
- 변동성: {result['portfolio_volatility']}%
- 최대 낙폭(MDD): {result['portfolio_max_drawdown']}%
- VaR(95%): {result['portfolio_var_95']}%
- Sharpe Ratio: {result['portfolio_sharpe_ratio']}

🔗 분산 효과:
- 평균 상관계수: {result['average_correlation']} (낮을수록 분산 효과 ↑)
- 분산 비율: {result['diversification_ratio']:.2f}x (1.0 미만이 이상적)

💡 해석:
- 분산 비율이 {result['diversification_ratio']:.2f}x로, {'우수한' if result['diversification_ratio'] < 0.8 else '보통' if result['diversification_ratio'] < 1.0 else '미흡한'} 분산 효과를 보입니다.
- 평균 상관계수 {result['average_correlation']:.2f}는 종목 간 {'낮은' if result['average_correlation'] < 0.3 else '보통' if result['average_correlation'] < 0.7 else '높은'} 연관성을 의미합니다.
"""
                    result['summary'] = summary.strip()

                return json.dumps(result, ensure_ascii=False, indent=2)

            else:
                return json.dumps({
                    'status': 'error',
                    'message': f'알 수 없는 명령어: {command}. risk 또는 portfolio를 사용하세요.'
                }, ensure_ascii=False, indent=2)

        except Exception as e:
            return json.dumps({
                'status': 'error',
                'message': f'오류 발생: {str(e)}'
            }, ensure_ascii=False, indent=2)


# 테스트 코드
if __name__ == "__main__":
    print("=== RiskAnalysisTool 테스트 ===\n")

    tool = RiskAnalysisTool()

    # 1. 단일 종목 분석
    print("1. 단일 종목 리스크 분석")
    print("-" * 50)
    result = tool.run("risk 005930")
    result_json = json.loads(result)
    if 'summary' in result_json:
        print(result_json['summary'])
    else:
        print(result)

    print("\n" + "="*70 + "\n")

    # 2. 포트폴리오 분석 (동일가중)
    print("2. 포트폴리오 리스크 분석 (동일가중)")
    print("-" * 50)
    result = tool.run("portfolio 005930,000660,035720")
    result_json = json.loads(result)
    if 'summary' in result_json:
        print(result_json['summary'])
    else:
        print(result)

    print("\n" + "="*70 + "\n")

    # 3. 포트폴리오 분석 (가중치 지정)
    print("3. 포트폴리오 리스크 분석 (커스텀 가중치)")
    print("-" * 50)
    result = tool.run("portfolio 005930,000660,035720 0.5,0.3,0.2")
    result_json = json.loads(result)
    if 'summary' in result_json:
        print(result_json['summary'])
    else:
        print(result)

    print("\n=== 테스트 완료 ===")
