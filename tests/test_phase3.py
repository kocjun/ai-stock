"""
Phase 3 통합 테스트 스크립트

Risk Manager와 Portfolio Planner 모듈 테스트
"""

import sys
import json
from datetime import datetime


def test_risk_analysis_module():
    """리스크 분석 모듈 테스트"""
    print("="*70)
    print("1. 리스크 분석 모듈 테스트")
    print("="*70)

    from risk_analysis import calculate_risk_score, analyze_portfolio_risk

    # 1-1. 단일 종목 리스크 분석
    print("\n[1-1] 단일 종목 리스크 분석 (005930)")
    result = calculate_risk_score('005930', days=252)

    if result['status'] == 'success':
        print(f"✓ 변동성: {result['volatility']}%")
        print(f"✓ MDD: {result['max_drawdown']}%")
        print(f"✓ VaR(95%): {result['var_95']}%")
        print(f"✓ Sharpe Ratio: {result['sharpe_ratio']}")
        print(f"✓ 리스크 점수: {result['risk_score']}/10")
        print(f"✓ 리스크 등급: {result['risk_grade']}")
    else:
        print(f"✗ 실패: {result['message']}")
        return False

    # 1-2. 포트폴리오 리스크 분석
    print("\n[1-2] 포트폴리오 리스크 분석")
    portfolio_result = analyze_portfolio_risk(
        stock_codes=['005930', '000660', '035720'],
        weights=[0.4, 0.3, 0.3]
    )

    if portfolio_result['status'] == 'success':
        print(f"✓ 포트폴리오 변동성: {portfolio_result['portfolio_volatility']}%")
        print(f"✓ 포트폴리오 MDD: {portfolio_result['portfolio_max_drawdown']}%")
        print(f"✓ Sharpe Ratio: {portfolio_result['portfolio_sharpe_ratio']}")
        print(f"✓ 분산 효과: {portfolio_result['diversification_ratio']:.2f}x")
    else:
        print(f"✗ 실패: {portfolio_result['message']}")
        return False

    print("\n✅ 리스크 분석 모듈 테스트 통과")
    return True


def test_portfolio_optimization_module():
    """포트폴리오 최적화 모듈 테스트"""
    print("\n" + "="*70)
    print("2. 포트폴리오 최적화 모듈 테스트")
    print("="*70)

    from portfolio_optimization import (
        create_equal_weight_portfolio,
        create_risk_parity_portfolio,
        check_sector_diversification,
        simulate_portfolio_performance
    )

    test_stocks = ['005930', '000660', '035720']

    # 2-1. 동일가중 포트폴리오
    print("\n[2-1] 동일가중 포트폴리오")
    equal_result = create_equal_weight_portfolio(test_stocks)

    if equal_result['status'] == 'success':
        print(f"✓ 방식: {equal_result['method']}")
        print(f"✓ 종목 수: {equal_result['num_stocks']}")
        print(f"✓ 비중: {equal_result['weights']}")
    else:
        print(f"✗ 실패: {equal_result['message']}")
        return False

    # 2-2. 리스크 패리티 포트폴리오
    print("\n[2-2] 리스크 패리티 포트폴리오")
    risk_parity_result = create_risk_parity_portfolio(test_stocks)

    if risk_parity_result['status'] == 'success':
        print(f"✓ 방식: {risk_parity_result['method']}")
        print(f"✓ 종목 수: {risk_parity_result['num_stocks']}")
        for code, weight in risk_parity_result['weights'].items():
            vol = risk_parity_result['volatilities'].get(code, 0)
            print(f"  - {code}: {weight*100:.2f}% (변동성: {vol}%)")
    else:
        print(f"✗ 실패: {risk_parity_result['message']}")
        return False

    # 2-3. 섹터 분산도
    print("\n[2-3] 섹터 분산도 체크")
    sector_result = check_sector_diversification(test_stocks)

    if sector_result['status'] == 'success':
        print(f"✓ 섹터 수: {sector_result['num_sectors']}")
        print(f"✓ 집중도(HHI): {sector_result['hhi']}")
        print(f"✓ 평가: {sector_result['concentration_level']}")
    else:
        print(f"✗ 실패: {sector_result['message']}")
        return False

    # 2-4. 성과 시뮬레이션
    print("\n[2-4] 성과 시뮬레이션")
    if equal_result['status'] == 'success':
        perf_result = simulate_portfolio_performance(test_stocks, equal_result['weights'])

        if perf_result['status'] == 'success':
            print(f"✓ 총 수익률: {perf_result['total_return']}%")
            print(f"✓ 연평균 수익률: {perf_result['annualized_return']}%")
            print(f"✓ 변동성: {perf_result['volatility']}%")
            print(f"✓ Sharpe Ratio: {perf_result['sharpe_ratio']}")
        else:
            print(f"✗ 실패: {perf_result['message']}")
            return False

    print("\n✅ 포트폴리오 최적화 모듈 테스트 통과")
    return True


def test_risk_analysis_tool():
    """RiskAnalysisTool 테스트"""
    print("\n" + "="*70)
    print("3. RiskAnalysisTool 테스트")
    print("="*70)

    from tools.risk_analysis_tool import RiskAnalysisTool

    tool = RiskAnalysisTool()

    # 3-1. 단일 종목 분석
    print("\n[3-1] 단일 종목 분석")
    result = tool.run("risk 005930")
    result_json = json.loads(result)

    if result_json['status'] == 'success':
        print("✓ RiskAnalysisTool 정상 작동")
        if 'summary' in result_json:
            print(result_json['summary'][:200] + "...")
    else:
        print(f"✗ 실패: {result_json['message']}")
        return False

    # 3-2. 포트폴리오 분석
    print("\n[3-2] 포트폴리오 분석")
    result = tool.run("portfolio 005930,000660,035720 0.4,0.3,0.3")
    result_json = json.loads(result)

    if result_json['status'] == 'success':
        print("✓ 포트폴리오 분석 정상 작동")
    else:
        print(f"✗ 실패: {result_json['message']}")
        return False

    print("\n✅ RiskAnalysisTool 테스트 통과")
    return True


def test_portfolio_tool():
    """PortfolioTool 테스트"""
    print("\n" + "="*70)
    print("4. PortfolioTool 테스트")
    print("="*70)

    from tools.portfolio_tool import PortfolioTool

    tool = PortfolioTool()

    # 4-1. 동일가중 포트폴리오
    print("\n[4-1] 동일가중 포트폴리오")
    result = tool.run("equal 005930,000660,035720")
    result_json = json.loads(result)

    if result_json['status'] == 'success':
        print("✓ 동일가중 포트폴리오 생성 성공")
    else:
        print(f"✗ 실패: {result_json['message']}")
        return False

    # 4-2. 리스크 패리티
    print("\n[4-2] 리스크 패리티 포트폴리오")
    result = tool.run("risk_parity 005930,000660,035720")
    result_json = json.loads(result)

    if result_json['status'] == 'success':
        print("✓ 리스크 패리티 포트폴리오 생성 성공")
    else:
        print(f"✗ 실패: {result_json['message']}")
        return False

    # 4-3. 섹터 분산
    print("\n[4-3] 섹터 분산 체크")
    result = tool.run("sector 005930,000660,035720")
    result_json = json.loads(result)

    if result_json['status'] == 'success':
        print("✓ 섹터 분산 분석 성공")
    else:
        print(f"✗ 실패: {result_json['message']}")
        return False

    print("\n✅ PortfolioTool 테스트 통과")
    return True


def test_all_modules():
    """전체 모듈 통합 테스트"""
    print("\n" + "="*70)
    print("5. 전체 모듈 통합 테스트")
    print("="*70)

    test_stocks = ['005930', '000660', '035720']

    print(f"\n테스트 종목: {', '.join(test_stocks)}")

    # 5-1. 리스크 분석
    print("\n[5-1] 리스크 분석")
    from risk_analysis import calculate_risk_score

    risk_results = {}
    for code in test_stocks:
        result = calculate_risk_score(code)
        if result['status'] == 'success':
            risk_results[code] = result
            print(f"✓ {code}: 리스크 점수 {result['risk_score']}/10 ({result['risk_grade']})")
        else:
            print(f"✗ {code}: {result['message']}")
            return False

    # 5-2. 포트폴리오 구성
    print("\n[5-2] 포트폴리오 구성")
    from portfolio_optimization import create_equal_weight_portfolio, create_risk_parity_portfolio

    equal_portfolio = create_equal_weight_portfolio(test_stocks)
    risk_parity_portfolio = create_risk_parity_portfolio(test_stocks)

    if equal_portfolio['status'] == 'success' and risk_parity_portfolio['status'] == 'success':
        print("✓ 동일가중 포트폴리오 생성 성공")
        print("✓ 리스크 패리티 포트폴리오 생성 성공")
    else:
        print("✗ 포트폴리오 생성 실패")
        return False

    # 5-3. 포트폴리오 리스크 분석
    print("\n[5-3] 포트폴리오 리스크 분석")
    from risk_analysis import analyze_portfolio_risk

    equal_risk = analyze_portfolio_risk(test_stocks, list(equal_portfolio['weights'].values()))
    rp_risk = analyze_portfolio_risk(test_stocks, list(risk_parity_portfolio['weights'].values()))

    if equal_risk['status'] == 'success' and rp_risk['status'] == 'success':
        print(f"✓ 동일가중 - Sharpe: {equal_risk['portfolio_sharpe_ratio']:.3f}, "
              f"변동성: {equal_risk['portfolio_volatility']:.2f}%")
        print(f"✓ 리스크패리티 - Sharpe: {rp_risk['portfolio_sharpe_ratio']:.3f}, "
              f"변동성: {rp_risk['portfolio_volatility']:.2f}%")
    else:
        print("✗ 포트폴리오 리스크 분석 실패")
        return False

    # 5-4. 성과 시뮬레이션
    print("\n[5-4] 성과 시뮬레이션")
    from portfolio_optimization import simulate_portfolio_performance

    perf = simulate_portfolio_performance(test_stocks, equal_portfolio['weights'])

    if perf['status'] == 'success':
        print(f"✓ 총 수익률: {perf['total_return']}%")
        print(f"✓ 연평균 수익률: {perf['annualized_return']}%")
        print(f"✓ 최대 낙폭: {perf['max_drawdown']}%")
    else:
        print(f"✗ 성과 시뮬레이션 실패: {perf['message']}")
        return False

    print("\n✅ 전체 모듈 통합 테스트 통과")
    return True


def main():
    """메인 테스트 실행"""
    print("="*70)
    print("Phase 3 통합 테스트")
    print(f"실행 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)

    results = []

    # 테스트 실행
    tests = [
        ("리스크 분석 모듈", test_risk_analysis_module),
        ("포트폴리오 최적화 모듈", test_portfolio_optimization_module),
        ("RiskAnalysisTool", test_risk_analysis_tool),
        ("PortfolioTool", test_portfolio_tool),
        ("전체 모듈 통합", test_all_modules)
    ]

    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ {test_name} 테스트 중 오류: {str(e)}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))

    # 결과 요약
    print("\n" + "="*70)
    print("테스트 결과 요약")
    print("="*70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ 통과" if result else "❌ 실패"
        print(f"{status} - {test_name}")

    print("\n" + "-"*70)
    print(f"전체: {passed}/{total} 통과 ({passed/total*100:.1f}%)")
    print("="*70)

    if passed == total:
        print("\n🎉 모든 테스트 통과!")
        return 0
    else:
        print(f"\n⚠️ {total - passed}개 테스트 실패")
        return 1


if __name__ == "__main__":
    sys.exit(main())
