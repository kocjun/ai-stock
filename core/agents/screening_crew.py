"""한국 주식 투자 분석 AI 에이전트 - Screening Analyst"""

import os
from datetime import datetime
from crewai import Agent, Crew, Process, Task
from dotenv import load_dotenv

# 커스텀 도구 임포트
from core.tools.financial_analysis_tool import FinancialAnalysisTool, FactorWeightTool
from core.tools.technical_analysis_tool import TechnicalAnalysisTool
from core.tools.n8n_webhook_tool import N8nWebhookTool
from core.utils.llm_utils import build_llm, get_llm_mode


def build_screening_analyst_crew(
    top_n: int = 20,
    min_roe: float = 10,
    max_debt_ratio: float = 150
):
    """
    Screening Analyst 에이전트 Crew 생성

    Args:
        top_n: 선정할 상위 종목 수
        min_roe: 최소 ROE (%)
        max_debt_ratio: 최대 부채비율 (%)
    """
    llm = build_llm(mode=get_llm_mode())

    # 도구 초기화
    financial_tool = FinancialAnalysisTool()
    technical_tool = TechnicalAnalysisTool()
    weight_tool = FactorWeightTool()

    n8n_webhook_url = os.getenv("N8N_WEBHOOK_URL")
    webhook_tool = N8nWebhookTool(webhook_url=n8n_webhook_url) if n8n_webhook_url else None

    # Screening Analyst 에이전트
    screening_analyst = Agent(
        role="Screening Analyst (종목 선별 분석가)",
        goal="재무 지표와 기술적 분석을 종합하여 투자 가치가 높은 종목을 선별합니다",
        backstory="""
        당신은 15년 경력의 퀀트 애널리스트입니다.
        밸류, 성장, 모멘텀 등 다양한 투자 팩터를 조합하여
        체계적인 종목 선별 시스템을 구축하는 전문가입니다.

        데이터 기반의 객관적 분석을 통해 감정을 배제하고
        일관된 투자 기준으로 종목을 평가합니다.

        주의: 모든 분석 결과는 투자 참고용이며,
        최종 투자 판단은 투자자 본인의 책임입니다.
        """,
        llm=llm,
        tools=[financial_tool, technical_tool, weight_tool],
        verbose=True,
        allow_delegation=False,
    )

    # 태스크 1: 팩터 기반 종목 스크리닝
    screening_task = Task(
        description=f"""
        재무 팩터를 기반으로 투자 가치가 높은 종목을 선별하세요.

        **스크리닝 조건:**
        - 상위 {top_n}개 종목 선정
        - 최소 ROE: {min_roe}%
        - 최대 부채비율: {max_debt_ratio}%

        **실행 순서:**
        1. financial_analysis 도구로 "screen:{top_n},roe={min_roe},debt={max_debt_ratio}" 명령 실행
        2. 선정된 종목의 재무 지표 확인
        3. 팩터별 점수 분석

        **분석 관점:**
        - 밸류: 낮은 PER, PBR
        - 성장: 높은 매출/이익 성장률
        - 수익성: 높은 ROE, 영업이익률
        - 안정성: 낮은 부채비율

        **중요:**
        - 정확한 명령어 형식 사용
        - 종목 순위와 점수 포함
        - 섹터별 분포 확인
        """,
        expected_output=f"""
        종목 스크리닝 결과:
        - 선정된 종목 수: {top_n}개
        - 종목별 종합 점수 및 순위
        - 팩터별 점수 (밸류, 성장, 수익성, 안정성)
        - 주요 재무 지표
        - 섹터별 분포
        """,
        agent=screening_analyst,
    )

    # 태스크 2: 기술적 분석 검증
    technical_task = Task(
        description="""
        스크리닝된 상위 종목들의 기술적 지표를 분석하세요.

        **분석 대상:**
        - 이전 태스크에서 선정된 상위 10개 종목

        **실행 순서:**
        1. 선정된 종목들의 종목 코드를 추출
        2. technical_analysis 도구로 각 종목의 기술적 지표 확인
        3. 매매 시그널 및 추세 분석

        **분석 항목:**
        - 이동평균선 위치 (상승/하락 추세)
        - RSI (과매수/과매도)
        - MACD 시그널
        - 볼린저 밴드 위치
        - 변동성 수준

        **중요:**
        - 각 종목마다 개별 분석 수행
        - 기술적 시그널 (매수/매도) 명시
        - 주의가 필요한 종목 지적
        """,
        expected_output="""
        기술적 분석 결과:
        - 종목별 기술적 지표 요약
        - 매매 시그널 (매수/중립/매도)
        - 현재 추세 (상승/박스권/하락)
        - 변동성 수준
        - 주의사항 (있는 경우)
        """,
        agent=screening_analyst,
        context=[screening_task],
    )

    # 태스크 3: 종합 투자 리포트 작성
    report_task = Task(
        description="""
        재무 분석과 기술적 분석을 종합하여 투자 참고 리포트를 작성하세요.

        **리포트 구성:**
        1. 요약 (Executive Summary)
           - 스크리닝 조건 및 결과
           - 추천 종목 TOP 5

        2. 선정 종목 상세 분석
           - 종목별 재무 지표
           - 종목별 기술적 분석
           - 투자 포인트 및 리스크

        3. 섹터별 분석
           - 섹터 분포
           - 섹터별 특징

        4. 투자 전략 제안
           - 포트폴리오 구성 제안
           - 진입 타이밍 제안
           - 리스크 관리 방안

        5. 면책 조항
           - 참고용 정보임을 명시
           - 투자 책임은 투자자 본인에게 있음

        **형식:**
        - 마크다운 형식
        - 한국어로 작성
        - 명확하고 읽기 쉽게

        **중요:**
        - 구체적인 수치 포함
        - 객관적 근거 기반 작성
        - 과도한 낙관이나 비관 금지
        - 반드시 면책 조항 포함
        """,
        expected_output="""
        # 한국 주식 종목 스크리닝 리포트

        ## 요약
        - 스크리닝 일시
        - 스크리닝 조건
        - 선정 종목 수
        - TOP 5 추천 종목

        ## 선정 종목 분석
        ### 1위: [종목명] (코드)
        - 재무 지표
        - 기술적 분석
        - 투자 포인트
        - 리스크 요인

        (이하 반복...)

        ## 섹터 분석
        - 섹터별 분포
        - 특징 및 시사점

        ## 투자 전략
        - 포트폴리오 구성안
        - 진입 전략
        - 리스크 관리

        ## 면책 조항
        본 리포트는 참고용 정보이며...
        """,
        agent=screening_analyst,
        context=[screening_task, technical_task],
    )

    # Crew 생성
    crew = Crew(
        agents=[screening_analyst],
        tasks=[screening_task, technical_task, report_task],
        process=Process.sequential,
        verbose=True,
    )

    return crew, webhook_tool


def main():
    """메인 실행 함수"""
    print("=" * 80)
    print(" " * 25 + "한국 주식 투자 분석 AI 에이전트")
    print(" " * 27 + "Screening Analyst Phase")
    print("=" * 80)
    print(f"실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Ollama 서버 확인
    ollama_url = os.getenv("OPENAI_API_BASE", "http://127.0.0.1:11434")
    print(f"Ollama 서버: {ollama_url}")
    print(f"모델: {os.getenv('OPENAI_MODEL_NAME', 'llama3.1:8b')}\n")

    # 스크리닝 설정
    TOP_N = 20  # 상위 20개 종목
    MIN_ROE = 10  # 최소 ROE 10%
    MAX_DEBT = 150  # 최대 부채비율 150%

    print(f"스크리닝 조건:")
    print(f"  - 선정 종목 수: {TOP_N}")
    print(f"  - 최소 ROE: {MIN_ROE}%")
    print(f"  - 최대 부채비율: {MAX_DEBT}%\n")
    print("=" * 80)

    # Crew 실행
    try:
        crew, webhook_tool = build_screening_analyst_crew(
            top_n=TOP_N,
            min_roe=MIN_ROE,
            max_debt_ratio=MAX_DEBT
        )

        result = crew.kickoff()

        print("\n" + "=" * 80)
        print("실행 완료!")
        print("=" * 80)
        print("\n[최종 리포트]")
        print(result)

        # n8n webhook 전송
        if webhook_tool:
            print("\n" + "-" * 80)
            webhook_status = webhook_tool.run({
                "type": "screening_report",
                "top_n": TOP_N,
                "min_roe": MIN_ROE,
                "max_debt_ratio": MAX_DEBT,
                "report": str(result),
                "timestamp": datetime.now().isoformat()
            })
            print(webhook_status)
            print("-" * 80)

        # 리포트를 파일로 저장
        report_file = f"reports/screening_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        os.makedirs("reports", exist_ok=True)

        with open(report_file, "w", encoding="utf-8") as f:
            f.write(str(result))

        print(f"\n✅ 리포트 저장: {report_file}")

    except Exception as e:
        print(f"\n✗ 실행 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 80)
    print(f"종료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)


if __name__ == "__main__":
    main()
