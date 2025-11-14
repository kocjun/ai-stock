"""
포트폴리오 최적화 CrewAI 도구

포트폴리오 구성, 최적화, 리밸런싱 제안
"""

from crewai.tools import BaseTool
from typing import Any
import json
from core.modules.portfolio_optimization import (
    create_equal_weight_portfolio,
    create_market_cap_weight_portfolio,
    create_risk_parity_portfolio,
    check_sector_diversification,
    simulate_portfolio_performance,
    suggest_rebalancing
)


class PortfolioTool(BaseTool):
    name: str = "portfolio_optimizer"
    description: str = """
    포트폴리오를 구성하고 최적화합니다.

    사용법:
    - 동일가중 포트폴리오: equal <종목코드1>,<종목코드2>,...
      예: equal 005930,000660,035720

    - 리스크 패리티: risk_parity <종목코드1>,<종목코드2>,...
      예: risk_parity 005930,000660,035720

    - 섹터 분산 체크: sector <종목코드1>,<종목코드2>,...
      예: sector 005930,000660,035720

    - 성과 시뮬레이션: simulate <종목코드1>,<종목코드2>,... <비중1>,<비중2>,...
      예: simulate 005930,000660,035720 0.4,0.3,0.3

    - 리밸런싱 제안: rebalance <현재비중> <목표비중>
      예: rebalance 005930:0.5,000660:0.3,035720:0.2 005930:0.4,000660:0.3,035720:0.3

    출력:
    - 포트폴리오 구성 및 비중
    - 섹터 분산도
    - 예상 성과 (수익률, 리스크)
    """

    def _run(self, argument: str) -> str:
        """
        포트폴리오 최적화 실행

        Args:
            argument: 명령어 문자열

        Returns:
            결과 (JSON 형식의 문자열)
        """
        try:
            parts = argument.strip().split()

            if len(parts) == 0:
                return json.dumps({
                    'status': 'error',
                    'message': '명령어를 입력하세요. 예: equal 005930,000660,035720'
                }, ensure_ascii=False, indent=2)

            command = parts[0].lower()

            # 동일가중 포트폴리오
            if command == 'equal':
                if len(parts) < 2:
                    return json.dumps({
                        'status': 'error',
                        'message': '종목 코드를 입력하세요. 예: equal 005930,000660,035720'
                    }, ensure_ascii=False, indent=2)

                stock_codes = parts[1].split(',')
                result = create_equal_weight_portfolio(stock_codes)

                if result['status'] == 'success':
                    summary = f"""
✓ 동일가중 포트폴리오 생성 완료

📦 포트폴리오 구성:
- 종목 수: {result['num_stocks']}개
- 비중: 각 {100/result['num_stocks']:.2f}%
- 종목: {', '.join(result['stocks'])}

🏢 섹터 분포:
{self._format_sector_distribution(result['sector_distribution'])}
"""
                    result['summary'] = summary.strip()

                return json.dumps(result, ensure_ascii=False, indent=2)

            # 리스크 패리티 포트폴리오
            elif command == 'risk_parity':
                if len(parts) < 2:
                    return json.dumps({
                        'status': 'error',
                        'message': '종목 코드를 입력하세요. 예: risk_parity 005930,000660,035720'
                    }, ensure_ascii=False, indent=2)

                stock_codes = parts[1].split(',')
                result = create_risk_parity_portfolio(stock_codes)

                if result['status'] == 'success':
                    weight_str = '\n'.join([f"  - {code}: {result['weights'][code]*100:.2f}% (변동성: {result['volatilities'].get(code, 0)}%)"
                                           for code in result['stocks']])

                    summary = f"""
✓ 리스크 패리티 포트폴리오 생성 완료

📦 포트폴리오 구성 (변동성 기반):
- 종목 수: {result['num_stocks']}개
{weight_str}

💡 설명:
- 각 종목의 변동성에 반비례하여 비중 조정
- 낮은 변동성 종목에 높은 비중 배분
- 포트폴리오 전체 리스크 균형 유지

🏢 섹터 분포:
{self._format_sector_distribution(result['sector_distribution'])}
"""
                    result['summary'] = summary.strip()

                return json.dumps(result, ensure_ascii=False, indent=2)

            # 섹터 분산 체크
            elif command == 'sector':
                if len(parts) < 2:
                    return json.dumps({
                        'status': 'error',
                        'message': '종목 코드를 입력하세요. 예: sector 005930,000660,035720'
                    }, ensure_ascii=False, indent=2)

                stock_codes = parts[1].split(',')
                result = check_sector_diversification(stock_codes)

                if result['status'] == 'success':
                    sector_str = '\n'.join([f"  - {sector}: {ratio}%"
                                           for sector, ratio in result['sector_ratios'].items()])

                    summary = f"""
✓ 섹터 분산도 분석 완료

🏢 섹터 분포:
- 총 섹터 수: {result['num_sectors']}개
{sector_str}

📊 집중도 분석:
- HHI 지수: {result['hhi']} (낮을수록 분산 우수)
- 평가: {result['concentration_level']}

💡 권장사항:
{result['recommendation']}
"""
                    result['summary'] = summary.strip()

                return json.dumps(result, ensure_ascii=False, indent=2)

            # 성과 시뮬레이션
            elif command == 'simulate':
                if len(parts) < 3:
                    return json.dumps({
                        'status': 'error',
                        'message': '종목 코드와 비중을 입력하세요. 예: simulate 005930,000660,035720 0.4,0.3,0.3'
                    }, ensure_ascii=False, indent=2)

                stock_codes = parts[1].split(',')
                try:
                    weights_list = [float(w) for w in parts[2].split(',')]
                except ValueError:
                    return json.dumps({
                        'status': 'error',
                        'message': '비중은 숫자로 입력하세요. 예: 0.4,0.3,0.3'
                    }, ensure_ascii=False, indent=2)

                if len(stock_codes) != len(weights_list):
                    return json.dumps({
                        'status': 'error',
                        'message': '종목 수와 비중 수가 일치해야 합니다'
                    }, ensure_ascii=False, indent=2)

                weights = {code: weight for code, weight in zip(stock_codes, weights_list)}

                result = simulate_portfolio_performance(stock_codes, weights)

                if result['status'] == 'success':
                    summary = f"""
✓ 포트폴리오 성과 시뮬레이션 완료

📈 수익률:
- 분석 기간: {result['period_days']}일
- 총 수익률: {result['total_return']}%
- 연평균 수익률: {result['annualized_return']}%

📊 리스크:
- 변동성: {result['volatility']}%
- 최대 낙폭(MDD): {result['max_drawdown']}%

⚖️ 위험 대비 수익:
- Sharpe Ratio: {result['sharpe_ratio']}

📉 극단 시나리오:
- 최고 수익일: {result['best_day']}%
- 최악 손실일: {result['worst_day']}%

💡 해석:
- Sharpe Ratio {result['sharpe_ratio']:.2f}는 {'우수한' if result['sharpe_ratio'] > 1.0 else '보통' if result['sharpe_ratio'] > 0.5 else '부족한'} 위험 대비 수익을 의미합니다.
"""
                    result['summary'] = summary.strip()

                return json.dumps(result, ensure_ascii=False, indent=2)

            # 리밸런싱 제안
            elif command == 'rebalance':
                if len(parts) < 3:
                    return json.dumps({
                        'status': 'error',
                        'message': '현재 비중과 목표 비중을 입력하세요. 예: rebalance 005930:0.5,000660:0.3 005930:0.4,000660:0.3'
                    }, ensure_ascii=False, indent=2)

                try:
                    current_weights = dict([pair.split(':') for pair in parts[1].split(',')])
                    current_weights = {k: float(v) for k, v in current_weights.items()}

                    target_weights = dict([pair.split(':') for pair in parts[2].split(',')])
                    target_weights = {k: float(v) for k, v in target_weights.items()}
                except (ValueError, IndexError):
                    return json.dumps({
                        'status': 'error',
                        'message': '비중 형식이 올바르지 않습니다. 예: 005930:0.5,000660:0.3'
                    }, ensure_ascii=False, indent=2)

                threshold = float(parts[3]) if len(parts) > 3 else 0.05

                result = suggest_rebalancing(current_weights, target_weights, threshold)

                if result['status'] == 'success':
                    if result['needs_rebalancing']:
                        actions_str = '\n'.join([
                            f"  - {action['stock_code']}: {action['current_weight']}% → {action['target_weight']}% "
                            f"({action['action']} {action['diff']}%)"
                            for action in result['rebalancing_actions']
                        ])

                        summary = f"""
✓ 리밸런싱 분석 완료

⚠️ 리밸런싱 필요: {result['num_actions']}개 종목

📋 조정 사항:
{actions_str}

💡 임계값: {result['threshold']}% (이 이상 차이 나는 종목만 표시)
"""
                    else:
                        summary = f"""
✓ 리밸런싱 분석 완료

✅ 리밸런싱 불필요
- 모든 종목이 목표 비중 대비 ±{result['threshold']}% 이내
"""

                    result['summary'] = summary.strip()

                return json.dumps(result, ensure_ascii=False, indent=2)

            else:
                return json.dumps({
                    'status': 'error',
                    'message': f'알 수 없는 명령어: {command}. equal, risk_parity, sector, simulate, rebalance 중 선택하세요.'
                }, ensure_ascii=False, indent=2)

        except Exception as e:
            return json.dumps({
                'status': 'error',
                'message': f'오류 발생: {str(e)}'
            }, ensure_ascii=False, indent=2)

    def _format_sector_distribution(self, sector_dist: dict) -> str:
        """섹터 분포를 보기 좋게 포맷"""
        if not sector_dist:
            return "  (섹터 정보 없음)"

        lines = []
        for sector, count in sector_dist.items():
            lines.append(f"  - {sector}: {count}개")
        return '\n'.join(lines)


# 테스트 코드
if __name__ == "__main__":
    print("=== PortfolioTool 테스트 ===\n")

    tool = PortfolioTool()

    # 1. 동일가중 포트폴리오
    print("1. 동일가중 포트폴리오")
    print("-" * 70)
    result = tool.run("equal 005930,000660,035720")
    result_json = json.loads(result)
    if 'summary' in result_json:
        print(result_json['summary'])
    else:
        print(result)

    print("\n" + "="*70 + "\n")

    # 2. 리스크 패리티 포트폴리오
    print("2. 리스크 패리티 포트폴리오")
    print("-" * 70)
    result = tool.run("risk_parity 005930,000660,035720")
    result_json = json.loads(result)
    if 'summary' in result_json:
        print(result_json['summary'])
    else:
        print(result)

    print("\n" + "="*70 + "\n")

    # 3. 섹터 분산 체크
    print("3. 섹터 분산 체크")
    print("-" * 70)
    result = tool.run("sector 005930,000660,035720")
    result_json = json.loads(result)
    if 'summary' in result_json:
        print(result_json['summary'])
    else:
        print(result)

    print("\n" + "="*70 + "\n")

    # 4. 성과 시뮬레이션
    print("4. 성과 시뮬레이션")
    print("-" * 70)
    result = tool.run("simulate 005930,000660,035720 0.4,0.3,0.3")
    result_json = json.loads(result)
    if 'summary' in result_json:
        print(result_json['summary'])
    else:
        print(result)

    print("\n=== 테스트 완료 ===")
