"""
통합 워크플로 파이프라인

전체 투자 분석 프로세스를 통합:
Data Curator → Screening Analyst → Risk Manager → Portfolio Planner
"""

from crewai import Agent, Task, Crew, Process
from core.tools.data_collection_tool import DataCollectionTool
from core.tools.data_quality_tool import DataQualityTool
from core.tools.financial_analysis_tool import FinancialAnalysisTool
from core.tools.technical_analysis_tool import TechnicalAnalysisTool
from core.tools.risk_analysis_tool import RiskAnalysisTool
from core.tools.portfolio_tool import PortfolioTool
from core.tools.n8n_webhook_tool import N8nWebhookTool
from core.utils.llm_utils import build_llm, get_llm_mode
from dotenv import load_dotenv
import os
import json
from datetime import datetime

# 환경 변수 로드
load_dotenv()


def create_integrated_investment_crew(market: str = "KOSPI", limit: int = 10, top_n: int = 5):
    """
    통합 투자 분석 Crew 생성

    Args:
        market: 시장 (KOSPI/KOSDAQ)
        limit: 수집할 종목 수
        top_n: 스크리닝 결과 상위 종목 수

    Returns:
        Crew 객체
    """
    llm = build_llm(mode=get_llm_mode())

    # 도구 초기화
    data_collection_tool = DataCollectionTool()
    data_quality_tool = DataQualityTool()
    financial_tool = FinancialAnalysisTool()
    technical_tool = TechnicalAnalysisTool()
    risk_tool = RiskAnalysisTool()
    portfolio_tool = PortfolioTool()
    webhook_tool = N8nWebhookTool(webhook_url=os.getenv("N8N_WEBHOOK_URL"))

    # 에이전트 정의
    # 1. Data Curator
    data_curator = Agent(
        role="Data Curator",
        goal="최신 시장 데이터를 수집하고 품질을 보장합니다",
        backstory="금융 데이터 엔지니어로 10년 경력. 데이터 정확성과 신뢰성을 최우선으로 합니다.",
        llm=llm,
        tools=[data_collection_tool, data_quality_tool],
        verbose=True,
        allow_delegation=False
    )

    # 2. Screening Analyst
    screening_analyst = Agent(
        role="Screening Analyst",
        goal="팩터 기반으로 유망 종목을 발굴합니다",
        backstory="퀀트 애널리스트로 15년 경력. 재무/기술적 분석을 통한 종목 발굴 전문가입니다.",
        llm=llm,
        tools=[financial_tool, technical_tool],
        verbose=True,
        allow_delegation=False
    )

    # 3. Risk Manager
    risk_manager = Agent(
        role="Risk Manager",
        goal="투자 리스크를 평가하고 관리 방안을 제시합니다",
        backstory="리스크 관리 전문가로 20년 경력. 손실 최소화와 안정적 수익 추구를 목표로 합니다.",
        llm=llm,
        tools=[risk_tool],
        verbose=True,
        allow_delegation=False
    )

    # 4. Portfolio Planner
    portfolio_planner = Agent(
        role="Portfolio Planner",
        goal="최적의 포트폴리오를 구성하고 투자 전략을 수립합니다",
        backstory="포트폴리오 매니저로 25년 경력. 자산배분과 리스크 관리에 정통합니다.",
        llm=llm,
        tools=[portfolio_tool, risk_tool],
        verbose=True,
        allow_delegation=False
    )

    # 태스크 정의
    # Phase 1: 데이터 수집
    data_collection_task = Task(
        description=f"""
        {market} 시장의 최신 데이터를 수집하세요.

        1. 종목 리스트 수집
           명령어: collect_stocks {market} {limit}

        2. 가격 데이터 수집
           명령어: collect_prices {market} 30 {limit}

        3. 데이터 품질 체크
           명령어: check_all

        수집된 종목 코드를 명확히 기록하세요.
        """,
        expected_output=f"{market} 시장 {limit}개 종목의 데이터 수집 완료 및 종목 코드 리스트",
        agent=data_curator
    )

    # Phase 2: 종목 스크리닝
    screening_task = Task(
        description=f"""
        수집된 종목들을 재무/기술적 분석을 통해 스크리닝하세요.

        1. 재무 분석 (상위 {top_n}개)
           - 밸류 팩터 (PER, PBR)
           - 성장 팩터 (매출/이익 성장률)
           - 수익성 팩터 (ROE, 영업이익률)

        2. 기술적 분석
           - 추세 분석 (이동평균)
           - 모멘텀 (RSI, MACD)

        3. 종합 평가
           - 팩터 스코어 기반 상위 {top_n}개 종목 선정
           - 각 종목의 투자 포인트 요약

        선정된 종목 코드를 명확히 나열하세요.
        """,
        expected_output=f"투자 유망 종목 상위 {top_n}개 및 선정 근거",
        agent=screening_analyst,
        context=[data_collection_task]
    )

    # Phase 3: 리스크 분석
    risk_analysis_task = Task(
        description="""
        스크리닝된 종목들의 리스크를 분석하세요.

        1. 개별 종목 리스크 분석
           - 각 종목에 대해 변동성, MDD, VaR 계산
           - 리스크 등급 평가

        2. 포트폴리오 리스크 시뮬레이션
           - 선정 종목으로 구성된 포트폴리오 리스크
           - 분산 효과 분석

        3. 리스크 관리 제안
           - 고위험 종목에 대한 주의사항
           - 적정 투자 비중 제안

        리스크 평가 결과를 명확히 정리하세요.
        """,
        expected_output="개별 종목 및 포트폴리오 리스크 분석 결과",
        agent=risk_manager,
        context=[screening_task]
    )

    # Phase 4: 포트폴리오 구성
    portfolio_construction_task = Task(
        description=f"""
        최종 포트폴리오를 구성하고 투자 전략을 수립하세요.

        1. 포트폴리오 최적화
           - 동일가중 vs 리스크 패리티 비교
           - 최적 비중 결정
           - 섹터 분산 체크

        2. 성과 시뮬레이션
           - 과거 데이터 기반 예상 수익률/리스크
           - Sharpe Ratio 계산

        3. 투자 전략 수립
           - 초기 포트폴리오 구성안
           - 리밸런싱 주기 및 조건
           - 손절/익절 기준

        4. 모니터링 계획
           - 주간/월간 점검 사항
           - 리밸런싱 필요 조건

        실행 가능한 구체적인 투자 계획을 한국어로 작성하세요.
        """,
        expected_output="최종 포트폴리오 구성 및 투자 실행 계획 (한국어)",
        agent=portfolio_planner,
        context=[screening_task, risk_analysis_task]
    )

    # Phase 5: 최종 리포트
    final_report_task = Task(
        description=f"""
        전체 분석 결과를 종합하여 최종 투자 리포트를 작성하세요.

        리포트 구성:
        1. 요약 (Executive Summary)
           - 분석 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
           - 대상 시장: {market}
           - 분석 종목 수: {limit}개
           - 최종 선정: {top_n}개

        2. 선정 종목 및 근거
           - 각 종목의 투자 포인트
           - 재무/기술적 분석 요약

        3. 리스크 평가
           - 개별 종목 리스크
           - 포트폴리오 리스크

        4. 포트폴리오 전략
           - 추천 비중
           - 예상 수익률/리스크
           - 실행 계획

        5. 면책 조항
           - 본 분석은 참고 정보이며 투자 권유가 아님
           - 투자 판단과 손실은 투자자 책임

        리포트를 n8n_webhook으로 전송하세요.
        """,
        expected_output="최종 투자 리포트 및 n8n 전송 성공",
        agent=portfolio_planner,
        context=[data_collection_task, screening_task, risk_analysis_task, portfolio_construction_task]
    )

    # Crew 생성
    crew = Crew(
        agents=[data_curator, screening_analyst, risk_manager, portfolio_planner],
        tasks=[
            data_collection_task,
            screening_task,
            risk_analysis_task,
            portfolio_construction_task,
            final_report_task
        ],
        process=Process.sequential,
        verbose=True
    )

    return crew


def main():
    """메인 실행 함수"""
    print("=" * 80)
    print("통합 투자 분석 워크플로 실행")
    print("=" * 80)

    # 파라미터 설정
    import sys

    market = sys.argv[1] if len(sys.argv) > 1 else "KOSPI"
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    top_n = int(sys.argv[3]) if len(sys.argv) > 3 else 5

    print(f"\n[설정]")
    print(f"  시장: {market}")
    print(f"  분석 종목 수: {limit}개")
    print(f"  최종 선정: {top_n}개")
    print()

    # Crew 생성
    crew = create_integrated_investment_crew(market=market, limit=limit, top_n=top_n)

    # 실행
    print("-" * 80)
    print("워크플로 시작...")
    print("-" * 80)

    try:
        result = crew.kickoff()

        print("\n" + "=" * 80)
        print("워크플로 완료!")
        print("=" * 80)
        print("\n[최종 결과]")
        print(result)

        # 결과 저장
        output_dir = ".crewai/integrated"
        os.makedirs(output_dir, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"{output_dir}/investment_report_{timestamp}.txt"

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write("통합 투자 분석 리포트\n")
            f.write("="*80 + "\n\n")
            f.write(f"생성 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"시장: {market}\n")
            f.write(f"분석 종목: {limit}개\n")
            f.write(f"선정 종목: {top_n}개\n\n")
            f.write("-"*80 + "\n\n")
            f.write(str(result))
            f.write("\n\n" + "-"*80 + "\n")
            f.write("\n⚠️ 투자 유의사항\n")
            f.write("본 분석은 공개된 데이터를 기반으로 한 참고 정보이며,\n")
            f.write("투자 권유가 아닙니다. 모든 투자 판단과 그에 따른\n")
            f.write("손실은 투자자 본인의 책임입니다.\n")

        print(f"\n리포트 저장됨: {output_file}")

    except Exception as e:
        print(f"\n✗ 에러 발생: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
