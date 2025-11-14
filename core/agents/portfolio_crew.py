"""
Portfolio Planner 에이전트

포트폴리오 구성 및 최적화를 담당하는 AI 에이전트
- 포트폴리오 구성 제안
- 리밸런싱 전략 수립
- 성과 시뮬레이션
"""

from crewai import Agent, Task, Crew, Process
from core.tools.portfolio_tool import PortfolioTool
from core.tools.risk_analysis_tool import RiskAnalysisTool
from core.tools.n8n_webhook_tool import N8nWebhookTool
from core.utils.llm_utils import build_llm, get_llm_mode
from dotenv import load_dotenv
import os
import json
from datetime import datetime

# 환경 변수 로드
load_dotenv()


def create_portfolio_planner_crew(stock_codes: list, mode: str = "optimize"):
    """
    Portfolio Planner Crew 생성

    Args:
        stock_codes: 포트폴리오 구성 종목 코드 리스트
        mode: 'optimize' (최적화) 또는 'rebalance' (리밸런싱)

    Returns:
        Crew 객체
    """
    llm = build_llm(mode=get_llm_mode())

    # 도구 초기화
    portfolio_tool = PortfolioTool()
    risk_tool = RiskAnalysisTool()
    webhook_tool = N8nWebhookTool(webhook_url=os.getenv("N8N_WEBHOOK_URL"))

    # Portfolio Planner 에이전트 정의
    portfolio_planner = Agent(
        role="Portfolio Planner",
        goal="최적의 포트폴리오를 구성하고 리밸런싱 전략을 수립합니다",
        backstory="""
        당신은 20년 경력의 포트폴리오 매니저입니다.
        자산배분, 리스크 관리, 분산투자 전략에 정통하며
        투자자의 목표와 리스크 허용도에 맞는 포트폴리오를 설계합니다.

        최신 포트폴리오 이론과 실전 경험을 바탕으로
        명확하고 실행 가능한 투자 전략을 제시합니다.
        """,
        llm=llm,
        tools=[portfolio_tool, risk_tool],
        verbose=True,
        allow_delegation=False
    )

    # 태스크 정의
    if mode == "optimize":
        # 포트폴리오 최적화 모드
        if not stock_codes:
            stock_codes = ['005930', '000660', '035720']  # 기본값

        # 1. 여러 포트폴리오 전략 생성
        strategy_task = Task(
            description=f"""
            다음 종목들로 3가지 포트폴리오 전략을 생성하세요:
            종목: {', '.join(stock_codes)}

            1. 동일가중 포트폴리오
               명령어: equal {','.join(stock_codes)}

            2. 리스크 패리티 포트폴리오
               명령어: risk_parity {','.join(stock_codes)}

            3. 섹터 분산도 체크
               명령어: sector {','.join(stock_codes)}

            각 전략의 장단점을 파악하고 비교하세요.
            """,
            expected_output="3가지 포트폴리오 전략 및 특징 비교",
            agent=portfolio_planner
        )

        # 2. 리스크 분석
        risk_task = Task(
            description=f"""
            생성된 포트폴리오 전략들의 리스크를 분석하세요.

            각 전략(동일가중, 리스크 패리티)에 대해:
            1. risk_analyzer 도구로 포트폴리오 리스크 분석
               예: portfolio {','.join(stock_codes)}

            2. 변동성, MDD, Sharpe Ratio 비교
            3. 분산 효과 평가

            리스크 관점에서 어느 전략이 우수한지 평가하세요.
            """,
            expected_output="각 전략의 리스크 분석 및 비교",
            agent=portfolio_planner,
            context=[strategy_task]
        )

        # 3. 최종 추천
        recommendation_task = Task(
            description="""
            분석 결과를 바탕으로 최적의 포트폴리오 전략을 추천하세요.

            1. 추천 전략 선정
               - 동일가중 vs 리스크 패리티 중 선택
               - 선정 이유 명확히 설명

            2. 포트폴리오 구성안
               - 각 종목의 비중
               - 예상 수익률 및 리스크
               - 섹터 분산 평가

            3. 투자 전략
               - 초기 포트폴리오 구성 방법
               - 리밸런싱 주기 제안 (예: 월간, 분기)
               - 모니터링 포인트

            4. 주의사항
               - 리스크 요인
               - 시장 환경에 따른 대응 방안

            실용적이고 명확한 투자 전략을 한국어로 작성하세요.
            """,
            expected_output="최종 포트폴리오 전략 및 실행 계획 (한국어 리포트)",
            agent=portfolio_planner,
            context=[strategy_task, risk_task]
        )

        tasks = [strategy_task, risk_task, recommendation_task]

    elif mode == "rebalance":
        # 리밸런싱 모드
        # (현재 비중 정보가 필요하므로, 여기서는 동일가중 가정)

        current_analysis_task = Task(
            description=f"""
            현재 포트폴리오의 상태를 분석하세요:
            종목: {', '.join(stock_codes)}

            1. portfolio_optimizer 도구로 현재 포트폴리오 분석
               - 동일가중 기준 생성: equal {','.join(stock_codes)}
               - 섹터 분산 체크: sector {','.join(stock_codes)}

            2. risk_analyzer 도구로 리스크 분석
               - 포트폴리오 리스크: portfolio {','.join(stock_codes)}

            현재 포트폴리오의 강점과 약점을 파악하세요.
            """,
            expected_output="현재 포트폴리오 분석 결과",
            agent=portfolio_planner
        )

        rebalancing_task = Task(
            description="""
            리밸런싱 필요성을 평가하고 구체적인 방안을 제시하세요.

            1. 리밸런싱 필요성 판단
               - 비중 이탈 정도
               - 리스크 수준 변화
               - 섹터 집중도 변화

            2. 리밸런싱 제안
               - 조정이 필요한 종목
               - 목표 비중
               - 매매 방향 (매수/매도)

            3. 실행 계획
               - 리밸런싱 시점
               - 분할 매매 여부
               - 거래 비용 고려

            명확하고 실행 가능한 계획을 한국어로 작성하세요.
            """,
            expected_output="리밸런싱 제안 및 실행 계획 (한국어)",
            agent=portfolio_planner,
            context=[current_analysis_task]
        )

        tasks = [current_analysis_task, rebalancing_task]

    else:
        raise ValueError(f"지원하지 않는 모드: {mode}")

    # 리포트 전송 태스크
    report_task = Task(
        description=f"""
        포트폴리오 분석 결과를 최종 리포트로 정리하여 n8n webhook으로 전송하세요.

        리포트 형식:
        - 분석 모드: {mode}
        - 종목: {', '.join(stock_codes) if stock_codes else 'N/A'}
        - 분석 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        - 포트폴리오 전략
        - 비중 구성
        - 예상 성과 및 리스크
        - 실행 계획

        n8n_webhook 도구를 사용하여 결과를 JSON 형식으로 전송하세요.
        """,
        expected_output="n8n webhook 전송 성공 메시지",
        agent=portfolio_planner,
        context=tasks
    )

    tasks.append(report_task)

    # Crew 생성
    crew = Crew(
        agents=[portfolio_planner],
        tasks=tasks,
        process=Process.sequential,
        verbose=True
    )

    return crew


def main():
    """메인 실행 함수"""
    print("=" * 70)
    print("Portfolio Planner 에이전트 실행")
    print("=" * 70)

    # 분석 모드 선택
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == 'rebalance':
        # 리밸런싱 모드
        print("\n[모드] 포트폴리오 리밸런싱\n")

        stock_codes = ['005930', '000660', '035720']

        if len(sys.argv) > 2:
            stock_codes = sys.argv[2].split(',')

        print(f"분석 대상: {', '.join(stock_codes)}\n")

        crew = create_portfolio_planner_crew(stock_codes=stock_codes, mode='rebalance')
    else:
        # 최적화 모드
        print("\n[모드] 포트폴리오 최적화\n")

        stock_codes = ['005930', '000660', '035720']  # 기본값

        if len(sys.argv) > 1:
            stock_codes = sys.argv[1].split(',')

        print(f"분석 대상: {', '.join(stock_codes)}\n")

        crew = create_portfolio_planner_crew(stock_codes=stock_codes, mode='optimize')

    # Crew 실행
    print("-" * 70)
    print("분석 시작...")
    print("-" * 70)

    try:
        result = crew.kickoff()

        print("\n" + "=" * 70)
        print("분석 완료!")
        print("=" * 70)
        print("\n[최종 결과]")
        print(result)

        # 결과 저장
        output_dir = ".crewai/portfolio_planner"
        os.makedirs(output_dir, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"{output_dir}/report_{timestamp}.txt"

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(str(result))

        print(f"\n리포트 저장됨: {output_file}")

    except Exception as e:
        print(f"\n✗ 에러 발생: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
