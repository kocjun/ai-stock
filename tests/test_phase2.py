"""
Phase 2 통합 테스트 스크립트

재무 지표 계산, 팩터 스코어링, 기술적 분석 모듈을 테스트합니다.
실제 데이터베이스 연결이 필요합니다.
"""

import sys
import traceback
from datetime import datetime


def test_financial_metrics():
    """재무 지표 계산 모듈 테스트"""
    print("\n" + "=" * 80)
    print("1. 재무 지표 계산 모듈 테스트")
    print("=" * 80)

    try:
        from financial_metrics import (
            calculate_basic_ratios,
            calculate_profitability_metrics,
            calculate_growth_rates,
            get_financial_data_from_db,
            analyze_stock_fundamentals
        )
        import pandas as pd

        # 샘플 데이터로 테스트
        print("\n[1-1] 샘플 데이터로 계산 테스트")
        sample_data = pd.DataFrame({
            'code': ['TEST'],
            'revenue': [100000000],
            'operating_profit': [15000000],
            'net_profit': [10000000],
            'total_assets': [200000000],
            'total_equity': [120000000],
            'total_debt': [80000000],
            'market_cap': [150000000]
        })

        ratios = calculate_basic_ratios(sample_data)
        print(f"  ROE: {ratios['roe'].iloc[0]:.2f}%")
        print(f"  ROA: {ratios['roa'].iloc[0]:.2f}%")
        print(f"  부채비율: {ratios['debt_ratio'].iloc[0]:.2f}%")
        print(f"  PER: {ratios['per'].iloc[0]:.2f}")
        print(f"  PBR: {ratios['pbr'].iloc[0]:.2f}")

        profitability = calculate_profitability_metrics(ratios)
        print(f"  영업이익률: {profitability['operating_margin'].iloc[0]:.2f}%")
        print(f"  순이익률: {profitability['net_margin'].iloc[0]:.2f}%")

        print("\n✅ 재무 지표 계산 모듈 테스트 통과")
        return True

    except Exception as e:
        print(f"\n❌ 재무 지표 계산 모듈 테스트 실패: {e}")
        traceback.print_exc()
        return False


def test_factor_scoring():
    """팩터 스코어링 시스템 테스트"""
    print("\n" + "=" * 80)
    print("2. 팩터 스코어링 시스템 테스트")
    print("=" * 80)

    try:
        from factor_scoring import FactorScorer
        import pandas as pd
        import numpy as np

        print("\n[2-1] FactorScorer 초기화")
        scorer = FactorScorer()
        print(f"  가중치: {scorer.weights}")

        # 샘플 데이터
        print("\n[2-2] 샘플 데이터로 스코어링 테스트")
        sample_data = pd.DataFrame({
            'code': ['TEST1', 'TEST2', 'TEST3'],
            'name': ['테스트1', '테스트2', '테스트3'],
            'per': [10.0, 15.0, 20.0],
            'pbr': [1.0, 1.5, 2.0],
            'roe': [15.0, 12.0, 8.0],
            'operating_margin': [10.0, 8.0, 5.0],
            'revenue_growth': [15.0, 10.0, 5.0],
            'net_profit_growth': [20.0, 15.0, 10.0],
            'debt_ratio': [50.0, 80.0, 120.0],
            'volatility': [25.0, 30.0, 35.0]
        })

        # 각 팩터 점수 계산
        scored = scorer.calculate_value_score(sample_data)
        scored = scorer.calculate_growth_score(scored)
        scored = scorer.calculate_profitability_score(scored)
        scored = scorer.calculate_stability_score(scored)
        scored = scorer.calculate_composite_score(scored)

        print("\n  종합 점수:")
        for idx, row in scored.iterrows():
            print(f"    {row['name']}: {row['composite_score']:.1f}점")

        print("\n✅ 팩터 스코어링 시스템 테스트 통과")
        return True

    except Exception as e:
        print(f"\n❌ 팩터 스코어링 시스템 테스트 실패: {e}")
        traceback.print_exc()
        return False


def test_technical_indicators():
    """기술적 지표 모듈 테스트"""
    print("\n" + "=" * 80)
    print("3. 기술적 지표 모듈 테스트")
    print("=" * 80)

    try:
        from technical_indicators import (
            calculate_sma,
            calculate_ema,
            calculate_rsi,
            calculate_macd,
            calculate_bollinger_bands
        )
        import pandas as pd
        import numpy as np

        # 샘플 가격 데이터 생성
        print("\n[3-1] 샘플 가격 데이터 생성")
        np.random.seed(42)
        dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
        prices = 50000 + np.cumsum(np.random.randn(100) * 500)

        sample_data = pd.DataFrame({
            'date': dates,
            'close': prices
        })

        print(f"  데이터 기간: {dates[0]} ~ {dates[-1]}")
        print(f"  데이터 건수: {len(sample_data)}")

        # 지표 계산
        print("\n[3-2] 기술적 지표 계산")
        sample_data['sma_20'] = calculate_sma(sample_data, 'close', 20)
        sample_data['ema_20'] = calculate_ema(sample_data, 'close', 20)
        sample_data['rsi'] = calculate_rsi(sample_data, 'close', 14)

        macd, signal, histogram = calculate_macd(sample_data)
        sample_data['macd'] = macd

        upper, middle, lower = calculate_bollinger_bands(sample_data)
        sample_data['bb_upper'] = upper

        # 최신 데이터
        latest = sample_data.iloc[-1]
        print(f"  종가: {latest['close']:.0f}")
        print(f"  SMA(20): {latest['sma_20']:.0f}")
        print(f"  EMA(20): {latest['ema_20']:.0f}")
        print(f"  RSI(14): {latest['rsi']:.2f}")
        print(f"  MACD: {latest['macd']:.4f}")
        print(f"  BB 상단: {latest['bb_upper']:.0f}")

        print("\n✅ 기술적 지표 모듈 테스트 통과")
        return True

    except Exception as e:
        print(f"\n❌ 기술적 지표 모듈 테스트 실패: {e}")
        traceback.print_exc()
        return False


def test_crewai_tools():
    """CrewAI 도구 테스트"""
    print("\n" + "=" * 80)
    print("4. CrewAI 도구 테스트")
    print("=" * 80)

    try:
        from tools.financial_analysis_tool import FinancialAnalysisTool
        from tools.technical_analysis_tool import TechnicalAnalysisTool

        print("\n[4-1] FinancialAnalysisTool 초기화")
        fin_tool = FinancialAnalysisTool()
        print(f"  도구명: {fin_tool.name}")
        print(f"  설명: {fin_tool.description[:50]}...")

        print("\n[4-2] TechnicalAnalysisTool 초기화")
        tech_tool = TechnicalAnalysisTool()
        print(f"  도구명: {tech_tool.name}")
        print(f"  설명: {tech_tool.description[:50]}...")

        print("\n✅ CrewAI 도구 테스트 통과")
        return True

    except Exception as e:
        print(f"\n❌ CrewAI 도구 테스트 실패: {e}")
        traceback.print_exc()
        return False


def test_database_connection():
    """데이터베이스 연결 테스트"""
    print("\n" + "=" * 80)
    print("5. 데이터베이스 연결 테스트")
    print("=" * 80)

    try:
        from db_utils import get_db_connection

        print("\n[5-1] 데이터베이스 연결")
        conn = get_db_connection()
        cur = conn.cursor()

        # 데이터 확인
        print("\n[5-2] 데이터 건수 확인")
        cur.execute("SELECT COUNT(*) FROM stocks")
        stock_count = cur.fetchone()[0]
        print(f"  종목 수: {stock_count}")

        cur.execute("SELECT COUNT(*) FROM prices")
        price_count = cur.fetchone()[0]
        print(f"  가격 데이터: {price_count}")

        cur.execute("SELECT COUNT(*) FROM financials")
        financial_count = cur.fetchone()[0]
        print(f"  재무 데이터: {financial_count}")

        cur.close()
        conn.close()

        if stock_count == 0:
            print("\n⚠️  경고: 종목 데이터가 없습니다. collect_data.py를 먼저 실행하세요.")
            return True  # 연결은 성공

        print("\n✅ 데이터베이스 연결 테스트 통과")
        return True

    except Exception as e:
        print(f"\n❌ 데이터베이스 연결 테스트 실패: {e}")
        traceback.print_exc()
        return False


def main():
    """메인 테스트 실행"""
    print("=" * 80)
    print(" " * 25 + "Phase 2 통합 테스트")
    print("=" * 80)
    print(f"실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    results = {
        "재무 지표 계산": False,
        "팩터 스코어링": False,
        "기술적 지표": False,
        "CrewAI 도구": False,
        "데이터베이스": False
    }

    # 테스트 실행
    results["데이터베이스"] = test_database_connection()
    results["재무 지표 계산"] = test_financial_metrics()
    results["팩터 스코어링"] = test_factor_scoring()
    results["기술적 지표"] = test_technical_indicators()
    results["CrewAI 도구"] = test_crewai_tools()

    # 결과 요약
    print("\n" + "=" * 80)
    print(" " * 30 + "테스트 결과 요약")
    print("=" * 80)

    all_passed = True
    for name, passed in results.items():
        status = "✅ 통과" if passed else "❌ 실패"
        print(f"  {name:20s}: {status}")
        if not passed:
            all_passed = False

    print("\n" + "=" * 80)
    if all_passed:
        print("🎉 모든 테스트 통과!")
        print("\n다음 단계:")
        print("  1. 재무 데이터가 없다면: collect_data.py 실행")
        print("  2. Screening Analyst 실행: python screening_crew.py")
    else:
        print("⚠️  일부 테스트 실패")
        print("실패한 항목을 확인하고 문제를 해결하세요.")

    print("=" * 80)
    print(f"종료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
