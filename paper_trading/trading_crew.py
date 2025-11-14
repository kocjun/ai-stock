"""
AI 에이전트 기반 자동 매매 시스템

integrated_crew의 분석 결과를 받아 실제 페이퍼 트레이딩 실행
"""

import sys
import re
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# 현재 디렉토리를 sys.path에 추가 (같은 디렉토리의 모듈 import용)
sys.path.insert(0, str(Path(__file__).parent))

from core.agents.integrated_crew import create_integrated_investment_crew
from core.utils.exclusion_manager import filter_excluded_recommendations
import paper_trading as pt
import portfolio_manager as pm
import ai_analysis_storage as ai_storage

# 함수들 가져오기
execute_buy = pt.execute_buy
execute_sell = pt.execute_sell
get_portfolio = pt.get_portfolio
update_portfolio_values = pt.update_portfolio_values
get_latest_price = pt.get_latest_price
save_daily_snapshot = pm.save_daily_snapshot
check_stop_loss_take_profit = pm.check_stop_loss_take_profit
calculate_portfolio_metrics = pm.calculate_portfolio_metrics


def parse_portfolio_recommendations(crew_output: str) -> List[Dict]:
    """
    Crew 출력에서 포트폴리오 추천 정보 파싱

    Args:
        crew_output: Crew 실행 결과 텍스트

    Returns:
        List[Dict]: 추천 종목 리스트
            - code: 종목 코드
            - weight: 추천 비중 (0-1)
            - reason: 선정 사유
    """
    recommendations = []

    # 종목 코드 패턴 (6자리 숫자)
    code_pattern = r'\b(\d{6})\b'

    # 비중 패턴 (예: 20%, 0.2)
    weight_pattern = r'(\d+\.?\d*)%'

    # 텍스트에서 종목 코드 추출
    codes = re.findall(code_pattern, crew_output)

    if not codes:
        print("⚠️  포트폴리오 추천 정보를 찾을 수 없습니다")
        return []

    # 중복 제거
    unique_codes = list(dict.fromkeys(codes))

    # 동일 가중 비중 계산 (기본)
    equal_weight = 1.0 / len(unique_codes) if unique_codes else 0

    for code in unique_codes:
        recommendations.append({
            'code': code,
            'weight': equal_weight,
            'reason': f"AI 분석 추천 (동일 가중)"
        })

    return recommendations


def extract_and_save_ai_analysis(crew_output: str, trade_results: List[Dict]) -> List[int]:
    """
    Crew 출력에서 AI 분석 정보 추출 및 저장

    Args:
        crew_output: Crew 실행 결과 텍스트
        trade_results: 실행된 거래 결과 리스트

    Returns:
        List[int]: 저장된 분석 ID 리스트
    """
    saved_analysis_ids = []

    try:
        # 간단한 패턴 기반 파싱 (향후 구조화된 JSON 출력으로 개선 가능)
        lines = crew_output.split('\n')

        for line in lines:
            # 종목 코드 찾기 (6자리 숫자)
            code_match = re.search(r'\b(\d{6})\b', line)
            if not code_match:
                continue

            code = code_match.group(1)

            # AI 분석 정보 추출 (기본값)
            analysis_data = {
                'code': code,
                'overall_score': 75.0,  # 기본값
                'financial_score': 74.0,
                'technical_score': 76.0,
                'risk_score': 70.0,
                'target_price': get_latest_price(code) * 1.1 if get_latest_price(code) else 0,
                'target_horizon_days': 90,
                'confidence_level': 75.0,
                'risk_grade': 'Medium',
                'volatility': 15.0,
                'max_drawdown': 10.0,
                'buy_rationale': f"AI 종합 분석 추천: {line[:100]}",
                'key_factors': {
                    'ai_recommendation': True,
                    'analysis_date': datetime.now().isoformat()
                },
                'technical_indicators': {},
                'financial_metrics': {},
                'analysis_source': 'integrated_crew'
            }

            # AI 분석 저장
            analysis_id = ai_storage.save_stock_ai_analysis(**analysis_data)

            if analysis_id:
                saved_analysis_ids.append(analysis_id)

                # 해당 거래와 연결
                for trade in trade_results:
                    if trade.get('code') == code:
                        ai_storage.AIAnalysisStorage.link_trade_to_analysis(
                            trade.get('trade_id'),
                            analysis_id,
                            influence_score=80.0
                        )

    except Exception as e:
        print(f"⚠️  AI 분석 저장 실패: {str(e)[:100]}")

    return saved_analysis_ids


def calculate_purchase_quantities(account_id: int, recommendations: List[Dict],
                                  cash_reserve_pct: float = 0.2) -> List[Dict]:
    """
    매수 수량 계산

    Args:
        account_id: 계좌 ID
        recommendations: 추천 종목 리스트
        cash_reserve_pct: 현금 보유 비율 (기본: 20%)

    Returns:
        List[Dict]: 매수 계획
            - code: 종목 코드
            - quantity: 매수 수량
            - target_amount: 목표 투자 금액
            - current_price: 현재가
    """
    # 가용 현금 계산
    current_balance = float(pt.get_current_balance(account_id))
    investable_cash = current_balance * (1 - cash_reserve_pct)

    purchase_plans = []

    for rec in recommendations:
        code = rec['code']
        weight = rec['weight']

        # 목표 투자 금액
        target_amount = investable_cash * weight

        # 현재가 조회
        current_price = get_latest_price(code)
        if current_price is None:
            print(f"⚠️  {code}: 가격 정보 없음, 건너뜀")
            continue

        # 매수 수량 계산 (수수료 고려)
        quantity = int(target_amount / (current_price * 1.00015))

        if quantity > 0:
            purchase_plans.append({
                'code': code,
                'quantity': quantity,
                'target_amount': target_amount,
                'current_price': current_price,
                'reason': rec['reason']
            })

    return purchase_plans


def execute_initial_portfolio(account_id: int, recommendations: List[Dict],
                              cash_reserve_pct: float = 0.2,
                              dry_run: bool = False) -> Dict:
    """
    초기 포트폴리오 구성 (전체 매수)

    Args:
        account_id: 계좌 ID
        recommendations: 추천 종목 리스트
        cash_reserve_pct: 현금 보유 비율
        dry_run: 테스트 모드 (실제 매수 안 함)

    Returns:
        Dict: 실행 결과
            - executed_trades: 체결된 거래
            - failed_trades: 실패한 거래
            - total_invested: 총 투자 금액
    """
    # 매수 계획 수립
    purchase_plans = calculate_purchase_quantities(account_id, recommendations, cash_reserve_pct)

    if not purchase_plans:
        return {
            'executed_trades': [],
            'failed_trades': [],
            'total_invested': 0,
            'message': "매수 가능한 종목이 없습니다"
        }

    print(f"\n{'='*60}")
    print(f"초기 포트폴리오 구성")
    print(f"{'='*60}")
    print(f"총 {len(purchase_plans)}개 종목 매수 예정\n")

    executed_trades = []
    failed_trades = []
    total_invested = 0

    for plan in purchase_plans:
        code = plan['code']
        quantity = plan['quantity']
        price = plan['current_price']

        print(f"📊 {code}: {quantity:,}주 @ {price:,.0f}원 = {quantity*price:,.0f}원")

        if dry_run:
            print(f"   [DRY RUN] 실제 매수 건너뜀\n")
            continue

        try:
            result = execute_buy(
                account_id=account_id,
                code=code,
                quantity=quantity,
                price=price,
                reason=plan['reason']
            )

            executed_trades.append({
                'code': code,
                'quantity': quantity,
                'price': result['price'],
                'amount': result['total_amount']
            })

            total_invested += result['total_amount']
            print(f"   ✅ 매수 체결: {result['total_amount']:,.0f}원\n")

        except Exception as e:
            failed_trades.append({
                'code': code,
                'quantity': quantity,
                'error': str(e)
            })
            print(f"   ❌ 매수 실패: {e}\n")

    print(f"{'='*60}")
    print(f"매수 완료: {len(executed_trades)}/{len(purchase_plans)}건")
    print(f"총 투자 금액: {total_invested:,.0f}원")
    print(f"{'='*60}\n")

    return {
        'executed_trades': executed_trades,
        'failed_trades': failed_trades,
        'total_invested': total_invested,
        'success_rate': len(executed_trades) / len(purchase_plans) if purchase_plans else 0
    }


def run_daily_trading_workflow(account_id: int = 1,
                               market: str = "KOSPI",
                               limit: int = 20,
                               top_n: int = 10,
                               cash_reserve_pct: float = 0.2,
                               stop_loss_pct: float = -10.0,
                               take_profit_pct: float = 20.0,
                               execute_trades: bool = False,
                               strategy: str = "ai") -> Dict:
    """
    일일 자동 매매 워크플로

    1. 포트폴리오 업데이트 및 손절/익절 체크
    2. AI 분석 OR 업종별 대장주 OR 주도주 전략 실행
    3. 매매 의사결정 및 실행
    4. 일일 스냅샷 저장

    Args:
        account_id: 계좌 ID
        market: 시장 (KOSPI/KOSDAQ)
        limit: 분석 종목 수 (AI 전략용)
        top_n: 선정 종목 수 (AI/주도주 전략용)
        cash_reserve_pct: 현금 보유 비율
        stop_loss_pct: 손절 기준
        take_profit_pct: 익절 기준
        execute_trades: 실제 매매 실행 여부 (False면 분석만)
        strategy: 투자 전략
                - ai: AI 기반 분석
                - sector: 업종별 대장주
                - hybrid: AI 50% + 대장주 50% 혼합
                - ai-sector: AI 기반 대장주 (거래량 중심)
                - leader: 팩터 스크리닝 기반 주도주 (리더십 점수 포함)

    Returns:
        Dict: 워크플로 결과
    """
    print("\n" + "="*80)
    print(f"📅 일일 자동 매매 워크플로 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    workflow_result = {
        'timestamp': datetime.now().isoformat(),
        'account_id': account_id,
        'steps': {}
    }

    # Step 1: 포트폴리오 업데이트
    print("\n[Step 1] 포트폴리오 업데이트")
    print("-"*60)
    try:
        update_result = update_portfolio_values(account_id)
        print(f"✅ {update_result['updated_count']}개 종목 업데이트 완료")
        print(f"   총 평가액: {update_result['total_value']:,.0f}원")
        workflow_result['steps']['portfolio_update'] = {
            'status': 'success',
            'data': update_result
        }
    except Exception as e:
        print(f"❌ 포트폴리오 업데이트 실패: {e}")
        workflow_result['steps']['portfolio_update'] = {
            'status': 'failed',
            'error': str(e)
        }

    # Step 2: 손절/익절 체크
    print("\n[Step 2] 손절/익절 체크")
    print("-"*60)
    try:
        exit_recommendations = check_stop_loss_take_profit(
            account_id, stop_loss_pct, take_profit_pct
        )

        if exit_recommendations:
            print(f"⚠️  매도 권장: {len(exit_recommendations)}개 종목")
            for rec in exit_recommendations:
                print(f"   • {rec['name']} ({rec['code']}): {rec['message']}")

            # 실제 매도 실행
            if execute_trades:
                print("\n   매도 실행 중...")
                for rec in exit_recommendations:
                    try:
                        result = execute_sell(
                            account_id=account_id,
                            code=rec['code'],
                            quantity=rec['quantity'],
                            reason=f"{rec['reason']}: {rec['message']}"
                        )
                        print(f"   ✅ {rec['name']} 매도: {result['profit_loss']:+,.0f}원")
                    except Exception as e:
                        print(f"   ❌ {rec['name']} 매도 실패: {e}")
            else:
                print("   [DRY RUN] 실제 매도 건너뜀")

            workflow_result['steps']['exit_check'] = {
                'status': 'action_needed',
                'recommendations': exit_recommendations
            }
        else:
            print("✅ 손절/익절 대상 없음")
            workflow_result['steps']['exit_check'] = {
                'status': 'success',
                'recommendations': []
            }
    except Exception as e:
        print(f"❌ 손절/익절 체크 실패: {e}")
        workflow_result['steps']['exit_check'] = {
            'status': 'failed',
            'error': str(e)
        }

    # Step 3: 투자 전략 선택 및 실행
    print(f"\n[Step 3] 투자 분석 (전략: {strategy.upper()})")
    print("-"*60)

    recommendations = []

    # 전략에 따라 분기
    if strategy == "sector":
        # 업종별 대장주 전략
        print("업종별 대장주 전략 실행\n")
        try:
            from sector_leader_strategy import get_sector_leader_recommendations
            recommendations = get_sector_leader_recommendations(
                num_sectors=5,
                leaders_per_sector=2
            )
            workflow_result['steps']['strategy'] = {
                'status': 'success',
                'type': 'sector_leader',
                'recommendations': recommendations
            }
        except Exception as e:
            print(f"❌ 업종별 대장주 전략 실패: {e}")
            workflow_result['steps']['strategy'] = {
                'status': 'failed',
                'error': str(e)
            }

    elif strategy == "ai-sector":
        # AI 기반 대장주 전략: 거래량 + 재무 + 기술적 분석
        print("AI 기반 대장주 전략 실행 (거래량 중심)\n")
        try:
            from ai_sector_leader_strategy import get_ai_sector_leader_recommendations
            recommendations = get_ai_sector_leader_recommendations(
                market=market,
                num_sectors=5,
                leaders_per_sector=1,
                min_volume_amount=50_000_000_000  # 500억원
            )
            workflow_result['steps']['strategy'] = {
                'status': 'success',
                'type': 'ai_sector_leader',
                'recommendations': recommendations
            }
        except Exception as e:
            print(f"❌ AI 기반 대장주 전략 실패: {e}")
            import traceback
            traceback.print_exc()
            workflow_result['steps']['strategy'] = {
                'status': 'failed',
                'error': str(e)
            }

    elif strategy == "leader":
        # 주도주 전략: 팩터 스크리닝 기반 리더십 점수 포함
        print("주도주 전략 실행 (팩터 기반 리더십 점수)\n")
        try:
            from leader_strategy import get_leader_recommendations
            recommendations = get_leader_recommendations(
                market=market,
                top_n=top_n,
                weights=None  # 기본 가중치 사용 (value/growth/profitability 각 20%, momentum 15%, stability 10%, leadership 15%)
            )
            workflow_result['steps']['strategy'] = {
                'status': 'success',
                'type': 'leader',
                'recommendations': recommendations
            }
        except Exception as e:
            print(f"❌ 주도주 전략 실패: {e}")
            import traceback
            traceback.print_exc()
            workflow_result['steps']['strategy'] = {
                'status': 'failed',
                'error': str(e)
            }

    elif strategy == "hybrid":
        # 하이브리드 전략: 50% AI + 50% 대장주
        print("하이브리드 전략 실행 (AI 50% + 대장주 50%)\n")
        try:
            # AI 추천
            print("1) AI 분석 실행...")
            crew = create_integrated_investment_crew(market=market, limit=limit, top_n=top_n//2)
            crew_result = crew.kickoff()
            ai_recommendations = parse_portfolio_recommendations(str(crew_result))

            # 대장주 추천
            print("\n2) 업종별 대장주 선정...")
            from sector_leader_strategy import get_sector_leader_recommendations
            sector_recommendations = get_sector_leader_recommendations(
                num_sectors=5,
                leaders_per_sector=1
            )

            # 결합 (각각 50% 비중)
            for rec in ai_recommendations:
                rec['weight'] = rec['weight'] * 0.5
                rec['reason'] = f"AI 추천 (50%): {rec['reason']}"

            for rec in sector_recommendations:
                rec['weight'] = rec['weight'] * 0.5
                rec['reason'] = f"대장주 (50%): {rec['reason']}"

            recommendations = ai_recommendations + sector_recommendations

            workflow_result['steps']['strategy'] = {
                'status': 'success',
                'type': 'hybrid',
                'ai_count': len(ai_recommendations),
                'sector_count': len(sector_recommendations),
                'recommendations': recommendations
            }

        except Exception as e:
            print(f"❌ 하이브리드 전략 실패: {e}")
            workflow_result['steps']['strategy'] = {
                'status': 'failed',
                'error': str(e)
            }

    else:  # strategy == "ai" (default)
        # AI 전략
        print(f"AI 투자 분석")
        print(f"시장: {market}, 분석: {limit}개, 선정: {top_n}개")
        print("분석 실행 중... (수 분 소요될 수 있습니다)\n")

        try:
            crew = create_integrated_investment_crew(market=market, limit=limit, top_n=top_n)
            crew_result = crew.kickoff()

            print("\n✅ AI 분석 완료")

            # 결과 파싱
            recommendations = parse_portfolio_recommendations(str(crew_result))

            workflow_result['steps']['strategy'] = {
                'status': 'success',
                'type': 'ai',
                'recommendations': recommendations
            }

        except Exception as e:
            print(f"❌ AI 분석 실패: {e}")
            workflow_result['steps']['strategy'] = {
                'status': 'failed',
                'error': str(e)
            }

    # 제외 종목 필터링 (모든 전략 공통)
    if recommendations:
        print(f"\n📊 추천 종목 ({len(recommendations)}개):")
        for rec in recommendations:
            print(f"   • {rec['code']}: {rec['weight']*100:.1f}%")

        print("\n🔍 제외 종목 필터링 중...")
        filtered_recommendations = filter_excluded_recommendations(recommendations)

        if len(filtered_recommendations) < len(recommendations):
            removed_count = len(recommendations) - len(filtered_recommendations)
            print(f"   ⚠️  {removed_count}개 종목이 제외 목록으로 인해 필터링되었습니다")

        recommendations = filtered_recommendations

        if recommendations:
            print(f"\n✅ 최종 추천 종목 ({len(recommendations)}개):")
            for rec in recommendations:
                print(f"   • {rec['code']}: {rec['weight']*100:.1f}%")
        else:
            print("\n⚠️  모든 추천 종목이 제외되었습니다")
    else:
        print("⚠️  추천 종목이 없습니다")

    # Step 4: 매수 실행 (새 추천이 있는 경우)
    if recommendations and execute_trades:
        print("\n[Step 4] 매수 실행")
        print("-"*60)

        try:
            trade_result = execute_initial_portfolio(
                account_id=account_id,
                recommendations=recommendations,
                cash_reserve_pct=cash_reserve_pct,
                dry_run=False
            )

            workflow_result['steps']['buy_execution'] = {
                'status': 'success',
                'data': trade_result
            }

        except Exception as e:
            print(f"❌ 매수 실행 실패: {e}")
            workflow_result['steps']['buy_execution'] = {
                'status': 'failed',
                'error': str(e)
            }
    elif recommendations:
        print("\n[Step 4] 매수 실행")
        print("-"*60)
        print("ℹ️  [DRY RUN] 실제 매수 건너뜀")
        workflow_result['steps']['buy_execution'] = {
            'status': 'skipped',
            'reason': 'dry_run'
        }

    # Step 5: 일일 스냅샷 저장
    print("\n[Step 5] 일일 스냅샷 저장")
    print("-"*60)
    try:
        snapshot = save_daily_snapshot(account_id)
        print(f"✅ 스냅샷 저장 완료")
        print(f"   총 자산: {snapshot['total_value']:,.0f}원")
        print(f"   수익률: {snapshot['return_pct']:+.2f}%")

        workflow_result['steps']['snapshot'] = {
            'status': 'success',
            'data': snapshot
        }
    except Exception as e:
        print(f"❌ 스냅샷 저장 실패: {e}")
        workflow_result['steps']['snapshot'] = {
            'status': 'failed',
            'error': str(e)
        }

    # 최종 요약
    print("\n" + "="*80)
    print("✅ 일일 워크플로 완료")
    print("="*80)

    try:
        metrics = calculate_portfolio_metrics(account_id)
        print(f"\n현재 자산: {metrics['total_value']:,.0f}원")
        print(f"총 수익: {metrics['total_return']:+,.0f}원 ({metrics['total_return_pct']:+.2f}%)")
        print(f"거래 횟수: {metrics['num_trades']}회")

        workflow_result['final_metrics'] = metrics
    except Exception as e:
        print(f"⚠️  최종 지표 계산 실패: {e}")

    print()

    return workflow_result


if __name__ == "__main__":
    """메인 실행"""
    import argparse

    parser = argparse.ArgumentParser(description="AI 기반 자동 매매 시스템")
    parser.add_argument("--account-id", type=int, default=1, help="계좌 ID")
    parser.add_argument("--market", default="KOSPI", choices=["KOSPI", "KOSDAQ"], help="시장")
    parser.add_argument("--limit", type=int, default=20, help="분석 종목 수")
    parser.add_argument("--top-n", type=int, default=10, help="선정 종목 수")
    parser.add_argument("--cash-reserve", type=float, default=0.2, help="현금 보유 비율 (0-1)")
    parser.add_argument("--stop-loss", type=float, default=-10.0, help="손절 기준 (%)")
    parser.add_argument("--take-profit", type=float, default=20.0, help="익절 기준 (%)")
    parser.add_argument("--strategy", choices=["ai", "sector", "hybrid", "ai-sector", "leader"], default="ai",
                       help="투자 전략 (ai=AI분석, sector=업종별대장주, hybrid=혼합, ai-sector=AI기반대장주, leader=주도주)")
    parser.add_argument("--execute", action="store_true", help="실제 매매 실행 (미지정시 분석만)")
    parser.add_argument("--save-log", action="store_true", help="결과 로그 저장")

    args = parser.parse_args()

    # 워크플로 실행
    result = run_daily_trading_workflow(
        account_id=args.account_id,
        market=args.market,
        limit=args.limit,
        top_n=args.top_n,
        cash_reserve_pct=args.cash_reserve,
        stop_loss_pct=args.stop_loss,
        take_profit_pct=args.take_profit,
        execute_trades=args.execute,
        strategy=args.strategy
    )

    # 로그 저장
    if args.save_log:
        log_dir = Path(__file__).parent / "logs"
        log_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = log_dir / f"trading_workflow_{timestamp}.json"

        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        print(f"📝 로그 저장: {log_file}")
