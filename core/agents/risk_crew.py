"""
Risk Manager 에이전트

리스크 분석 및 관리를 담당하는 AI 에이전트
- 종목별 리스크 분석
- 포트폴리오 리스크 평가
- 리스크 관리 제안 생성
"""

from crewai import Agent, Task, Crew, Process
from core.tools.risk_analysis_tool import RiskAnalysisTool
from core.tools.n8n_webhook_tool import N8nWebhookTool
from core.utils.llm_utils import build_llm, get_llm_mode
from dotenv import load_dotenv
import os
import json
from datetime import datetime

# 환경 변수 로드
load_dotenv()


def create_risk_manager_crew(stock_codes: list = None, mode: str = "single"):
    """
    Risk Manager Crew 생성

    Args:
        stock_codes: 분석할 종목 코드 리스트
        mode: 'single' (개별 종목 분석) 또는 'portfolio' (포트폴리오 분석)

    Returns:
        Crew 객체
    """
    llm = build_llm(mode=get_llm_mode())

    # 도구 초기화
    risk_tool = RiskAnalysisTool()
    webhook_tool = N8nWebhookTool(webhook_url=os.getenv("N8N_WEBHOOK_URL"))

    # Risk Manager 에이전트 정의
    risk_manager = Agent(
        role="Risk Manager",
        goal="투자 포트폴리오의 리스크를 정확히 평가하고 관리 방안을 제시합니다",
        backstory="""
        당신은 15년 경력의 리스크 관리 전문가입니다.
        변동성, MDD, VaR 등 다양한 리스크 지표를 활용하여
        투자자의 손실을 최소화하는 전략을 수립합니다.

        통계적 분석과 실무 경험을 바탕으로
        명확하고 실용적인 리스크 관리 제안을 제공합니다.
        """,
        llm=llm,
        tools=[risk_tool],
        verbose=True,
        allow_delegation=False
    )

    # 태스크 정의
    if mode == "single":
        # 개별 종목 리스크 분석
        if not stock_codes:
            stock_codes = ['005930']  # 기본값: 삼성전자

        analysis_task = Task(
            description=f"""
            다음 종목들의 리스크를 개별적으로 분석하세요:
            종목 코드: {', '.join(stock_codes)}

            각 종목에 대해:
            1. risk_analyzer 도구를 사용하여 리스크 분석 실행
            2. 변동성, MDD, VaR, Sharpe Ratio 등 주요 지표 확인
            3. 리스크 점수와 등급 파악
            4. 각 종목의 리스크 특성 요약

            명령어 예시: risk 005930
            """,
            expected_output="각 종목의 리스크 분석 결과 및 주요 지표 요약",
            agent=risk_manager
        )

        evaluation_task = Task(
            description="""
            분석된 리스크 정보를 바탕으로 투자자에게 다음 내용을 제공하세요:

            1. 리스크 수준 평가
               - 각 종목의 리스크 등급 (낮음/보통/높음/매우 높음)
               - 특히 주의해야 할 종목과 그 이유

            2. 리스크 관리 제안
               - 고위험 종목에 대한 대응 방안
               - 적정 투자 비중 제안
               - 손절선 및 목표가 제안 (변동성 기반)

            3. 경고 사항
               - 최대 낙폭이 큰 종목 경고
               - VaR 기준 예상 최대 손실
               - 변동성이 시장 평균 대비 높은 종목

            명확하고 실용적인 조언을 한국어로 작성하세요.
            """,
            expected_output="리스크 평가 및 관리 제안 (한국어 리포트)",
            agent=risk_manager,
            context=[analysis_task]
        )

        tasks = [analysis_task, evaluation_task]

    elif mode == "portfolio":
        # 포트폴리오 리스크 분석
        if not stock_codes:
            stock_codes = ['005930', '000660', '035720']  # 기본값

        portfolio_analysis_task = Task(
            description=f"""
            다음 종목들로 구성된 포트폴리오의 리스크를 분석하세요:
            종목 코드: {', '.join(stock_codes)}

            1. risk_analyzer 도구를 사용하여 포트폴리오 분석 실행
               명령어: portfolio {','.join(stock_codes)}

            2. 포트폴리오 전체의 변동성, MDD, Sharpe Ratio 확인
            3. 분산 효과 분석 (평균 상관계수, 분산 비율)
            4. 개별 종목 대비 포트폴리오의 리스크 감소 효과 평가
            """,
            expected_output="포트폴리오 리스크 분석 결과 및 분산 효과 평가",
            agent=risk_manager
        )

        recommendation_task = Task(
            description="""
            포트폴리오 리스크 분석을 바탕으로 다음 내용을 제공하세요:

            1. 포트폴리오 리스크 평가
               - 전체 변동성 수준
               - 최대 낙폭 예상
               - VaR 기준 최악 시나리오

            2. 분산 효과 평가
               - 종목 간 상관관계 분석
               - 분산 투자의 효과성 평가
               - 추가 분산이 필요한지 여부

            3. 리스크 관리 제안
               - 포트폴리오 전체 리스크를 낮추기 위한 방안
               - 비중 조정 제안 (선택)
               - 헷징 전략 제안 (선택)

            4. 모니터링 포인트
               - 주의 깊게 관찰해야 할 지표
               - 재조정이 필요한 시점

            실용적이고 명확한 조언을 한국어로 작성하세요.
            """,
            expected_output="포트폴리오 리스크 관리 제안 (한국어 리포트)",
            agent=risk_manager,
            context=[portfolio_analysis_task]
        )

        tasks = [portfolio_analysis_task, recommendation_task]

    else:
        raise ValueError(f"지원하지 않는 모드: {mode}")

    # 리포트 전송 태스크
    report_task = Task(
        description=f"""
        리스크 분석 결과를 최종 리포트로 정리하여 n8n webhook으로 전송하세요.

        리포트 형식:
        - 분석 모드: {mode}
        - 종목: {', '.join(stock_codes) if stock_codes else 'N/A'}
        - 분석 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        - 리스크 평가 내용
        - 주요 지표
        - 관리 제안

        n8n_webhook 도구를 사용하여 결과를 JSON 형식으로 전송하세요.
        """,
        expected_output="n8n webhook 전송 성공 메시지",
        agent=risk_manager,
        context=tasks
    )

    tasks.append(report_task)

    # Crew 생성
    crew = Crew(
        agents=[risk_manager],
        tasks=tasks,
        process=Process.sequential,
        verbose=True
    )

    return crew


def main():
    """메인 실행 함수"""
    print("=" * 70)
    print("Risk Manager 에이전트 실행")
    print("=" * 70)

    # 분석 모드 선택
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == 'portfolio':
        # 포트폴리오 모드
        print("\n[모드] 포트폴리오 리스크 분석\n")

        stock_codes = ['005930', '000660', '035720']  # 삼성전자, SK하이닉스, 카카오

        if len(sys.argv) > 2:
            stock_codes = sys.argv[2].split(',')

        print(f"분석 대상: {', '.join(stock_codes)}\n")

        crew = create_risk_manager_crew(stock_codes=stock_codes, mode='portfolio')
    else:
        # 단일 종목 모드
        print("\n[모드] 개별 종목 리스크 분석\n")

        stock_codes = ['005930', '000660']  # 기본값

        if len(sys.argv) > 1:
            stock_codes = sys.argv[1].split(',')

        print(f"분석 대상: {', '.join(stock_codes)}\n")

        crew = create_risk_manager_crew(stock_codes=stock_codes, mode='single')

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
        output_dir = ".crewai/risk_manager"
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
