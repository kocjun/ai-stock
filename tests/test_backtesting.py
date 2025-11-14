"""
백테스팅 모듈 테스트

backtesting.py와 BacktestingTool 테스트
"""

import sys
from datetime import datetime, timedelta
from backtesting import run_backtest, compare_strategies, generate_backtest_report
from tools.backtesting_tool import BacktestingTool


def test_backtest_module():
    """백테스팅 모듈 직접 테스트"""
    print("\n" + "="*60)
    print("테스트 1: 백테스팅 모듈 (backtesting.py)")
    print("="*60 + "\n")

    # 최근 3개월 데이터로 백테스트
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')

    print(f"백테스트 기간: {start_date} ~ {end_date}")
    print("전략: 동일가중 (Equal Weight)")
    print("종목수: 10개\n")

    result = run_backtest(
        start_date=start_date,
        end_date=end_date,
        strategy="equal_weight",
        top_n=10
    )

    if result['status'] == 'success':
        print("\n✅ 백테스트 성공!")
        print(f"총 수익률: {result['returns']['total_return']:.2f}%")
        print(f"CAGR: {result['returns']['cagr']:.2f}%")
        print(f"Sharpe Ratio: {result['returns']['sharpe_ratio']:.2f}")
        print(f"MDD: {result['returns']['max_drawdown']:.2f}%")
        print(f"KOSPI 대비 알파: {result['benchmark']['alpha']:.2f}%p")

        # 리포트 생성 테스트
        print("\n리포트 생성 중...")
        report_file = "reports/test_backtest.md"
        generate_backtest_report(result, report_file)
        print(f"✓ 리포트 저장: {report_file}")

        return True
    else:
        print(f"\n❌ 백테스트 실패: {result.get('message')}")
        return False


def test_strategy_comparison():
    """전략 비교 테스트"""
    print("\n" + "="*60)
    print("테스트 2: 전략 비교 (compare_strategies)")
    print("="*60 + "\n")

    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')

    print(f"비교 기간: {start_date} ~ {end_date}")
    print("전략: equal_weight, market_cap, risk_parity")
    print("종목수: 10개\n")

    result = compare_strategies(
        start_date=start_date,
        end_date=end_date,
        top_n=10
    )

    if result['status'] == 'success':
        print("\n✅ 전략 비교 성공!")
        print(f"\n최고 성과 전략: {result['best_strategy']} (Sharpe Ratio 기준)\n")

        print("전략별 성과:")
        print("-" * 60)
        for strategy, metrics in result['strategies'].items():
            print(f"\n▶ {strategy.upper()}")
            print(f"  총 수익률: {metrics['total_return']:+.2f}%")
            print(f"  CAGR: {metrics['cagr']:+.2f}%")
            print(f"  Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
            print(f"  MDD: {metrics['max_drawdown']:.2f}%")
            print(f"  알파: {metrics['alpha']:+.2f}%p")

        return True
    else:
        print("❌ 전략 비교 실패")
        return False


def test_backtesting_tool():
    """BacktestingTool 테스트"""
    print("\n" + "="*60)
    print("테스트 3: BacktestingTool (CrewAI 도구)")
    print("="*60 + "\n")

    tool = BacktestingTool()

    # 테스트 3-1: 빠른 백테스트
    print("테스트 3-1: quick 명령어")
    print("-" * 60)
    result = tool.run("quick:10")
    print(result)

    print("\n" + "="*60 + "\n")

    # 테스트 3-2: 단일 전략 백테스트
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d')

    print("테스트 3-2: backtest 명령어 (최근 2개월)")
    print("-" * 60)
    result = tool.run(f"backtest:equal_weight,{start_date},{end_date},10")
    print(result)

    print("\n" + "="*60 + "\n")

    # 테스트 3-3: 전략 비교
    print("테스트 3-3: compare 명령어")
    print("-" * 60)
    result = tool.run(f"compare:{start_date},{end_date},10")
    print(result)

    return True


def main():
    """전체 테스트 실행"""
    print("\n" + "="*60)
    print("백테스팅 시스템 통합 테스트")
    print("="*60)

    results = []

    try:
        # 테스트 1: 백테스팅 모듈
        results.append(("백테스팅 모듈", test_backtest_module()))
    except Exception as e:
        print(f"\n❌ 백테스팅 모듈 테스트 실패: {str(e)}")
        results.append(("백테스팅 모듈", False))

    try:
        # 테스트 2: 전략 비교
        results.append(("전략 비교", test_strategy_comparison()))
    except Exception as e:
        print(f"\n❌ 전략 비교 테스트 실패: {str(e)}")
        results.append(("전략 비교", False))

    try:
        # 테스트 3: BacktestingTool
        results.append(("BacktestingTool", test_backtesting_tool()))
    except Exception as e:
        print(f"\n❌ BacktestingTool 테스트 실패: {str(e)}")
        results.append(("BacktestingTool", False))

    # 결과 요약
    print("\n" + "="*60)
    print("테스트 결과 요약")
    print("="*60 + "\n")

    passed = 0
    failed = 0

    for name, result in results:
        status = "✅ 통과" if result else "❌ 실패"
        print(f"{name:20s} : {status}")
        if result:
            passed += 1
        else:
            failed += 1

    print(f"\n총 {len(results)}개 테스트: {passed}개 통과, {failed}개 실패")

    if failed == 0:
        print("\n🎉 모든 테스트 통과!")
        return 0
    else:
        print(f"\n⚠️ {failed}개 테스트 실패")
        return 1


if __name__ == "__main__":
    sys.exit(main())
