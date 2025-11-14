"""한국 주식 투자 분석 AI 에이전트 - Data Curator"""

import os
from datetime import datetime
from crewai import Agent, Crew, Process, Task
from dotenv import load_dotenv

# 커스텀 도구 임포트
from core.tools.data_collection_tool import DataCollectionTool
from core.tools.data_quality_tool import DataQualityTool
from core.tools.n8n_webhook_tool import N8nWebhookTool
from core.utils.llm_utils import build_llm, get_llm_mode


def build_data_curator_crew(market: str = "KOSPI", limit: int = 50, days: int = 30):
    """
    Data Curator 에이전트 Crew 생성

    Args:
        market: 수집할 시장 (KOSPI/KOSDAQ)
        limit: 수집할 종목 수
        days: 수집할 가격 데이터 기간 (일)
    """
    llm = build_llm(mode=get_llm_mode())

    # 도구 초기화
    data_collector = DataCollectionTool()
    quality_checker = DataQualityTool()

    n8n_webhook_url = os.getenv("N8N_WEBHOOK_URL")
    webhook_tool = N8nWebhookTool(webhook_url=n8n_webhook_url) if n8n_webhook_url else None

    # Data Curator 에이전트
    data_curator = Agent(
        role="Data Curator (데이터 큐레이터)",
        goal="한국 주식 시장의 최신 데이터를 수집하고 품질을 검증합니다",
        backstory="""
        당신은 10년 경력의 금융 데이터 엔지니어입니다.
        한국 증권시장의 데이터 구조를 완벽히 이해하고 있으며,
        데이터 품질 관리와 ETL 프로세스 구축에 전문성을 가지고 있습니다.
        수집된 데이터의 정확성과 완정성을 보장하는 것이 최우선 목표입니다.
        """,
        llm=llm,
        tools=[data_collector, quality_checker],
        verbose=True,
        allow_delegation=False,
    )

    # 태스크 1: 데이터 수집
    collection_task = Task(
        description=f"""
        한국 {market} 시장의 주식 데이터를 수집하세요.

        **수집 요구사항:**
        1. {market} 시장 상위 {limit}개 종목 리스트 수집
        2. 각 종목의 최근 {days}일 가격 데이터 수집
        3. 데이터 수집 과정의 성공/실패 건수 기록

        **실행 순서:**
        1. data_collector 도구를 사용하여 "collect_all {market} {limit} {days}" 명령 실행
        2. 수집 결과를 자세히 기록

        **중요:**
        - 정확한 명령어 형식을 사용하세요
        - 수집된 데이터의 통계를 포함하세요
        """,
        expected_output=f"""
        데이터 수집 결과 리포트:
        - 수집된 종목 수: N개
        - 수집된 가격 데이터: N rows
        - 성공/실패 건수
        - 수집 기간 정보
        """,
        agent=data_curator,
    )

    # 태스크 2: 데이터 품질 검증
    quality_task = Task(
        description="""
        수집된 데이터의 품질을 검증하고 리포트를 작성하세요.

        **검증 항목:**
        1. 전체 데이터 통계 (종목 수, 데이터 건수)
        2. 데이터 커버리지 (가격 데이터가 없는 종목 확인)
        3. 데이터 품질 이슈 (비정상 값, 결측치)
        4. 시장/섹터별 분포

        **실행 순서:**
        1. data_quality_checker 도구로 "check_all" 실행
        2. 발견된 이슈 상세 기록
        3. 개선 권고사항 작성

        **중요:**
        - 모든 품질 지표를 포함하세요
        - 이슈가 있으면 구체적으로 명시하세요
        """,
        expected_output="""
        데이터 품질 검증 리포트:
        - 전체 통계
        - 커버리지 분석
        - 품질 이슈 (있는 경우)
        - 개선 권고사항
        """,
        agent=data_curator,
        context=[collection_task],
    )

    # 태스크 3: 최종 리포트 작성
    report_task = Task(
        description="""
        데이터 수집 및 품질 검증 결과를 종합하여 최종 리포트를 작성하세요.

        **리포트 구성:**
        1. 요약 (Executive Summary)
        2. 수집 결과 상세
        3. 품질 검증 결과
        4. 다음 실행을 위한 권고사항

        **형식:**
        - 마크다운 형식으로 작성
        - 한국어로 작성
        - 명확하고 간결하게

        **중요:**
        - 숫자는 구체적으로 명시
        - 이슈가 있으면 우선순위와 함께 기록
        """,
        expected_output="""
        # 한국 주식 데이터 수집 리포트

        ## 요약
        - 수집 일시
        - 수집 종목 수
        - 전체 성공률

        ## 수집 결과
        - 상세 통계

        ## 품질 검증
        - 검증 결과

        ## 권고사항
        - 다음 액션
        """,
        agent=data_curator,
        context=[collection_task, quality_task],
    )

    # Crew 생성
    crew = Crew(
        agents=[data_curator],
        tasks=[collection_task, quality_task, report_task],
        process=Process.sequential,
        verbose=True,
    )

    return crew, webhook_tool


def main():
    """메인 실행 함수"""
    print("=" * 80)
    print(" " * 25 + "한국 주식 투자 분석 AI 에이전트")
    print(" " * 30 + "Data Curator Phase")
    print("=" * 80)
    print(f"실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Ollama 서버 확인
    ollama_url = os.getenv("OPENAI_API_BASE", "http://127.0.0.1:11434")
    print(f"Ollama 서버: {ollama_url}")
    print(f"모델: {os.getenv('OPENAI_MODEL_NAME', 'llama3.1:8b')}\n")

    # 수집 설정
    MARKET = "KOSPI"
    LIMIT = 50  # 테스트용 50개
    DAYS = 30

    print(f"수집 설정:")
    print(f"  - 시장: {MARKET}")
    print(f"  - 종목 수: {LIMIT}")
    print(f"  - 기간: 최근 {DAYS}일\n")
    print("=" * 80)

    # Crew 실행
    try:
        crew, webhook_tool = build_data_curator_crew(
            market=MARKET,
            limit=LIMIT,
            days=DAYS
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
                "type": "data_collection_report",
                "market": MARKET,
                "limit": LIMIT,
                "days": DAYS,
                "report": str(result),
                "timestamp": datetime.now().isoformat()
            })
            print(webhook_status)
            print("-" * 80)

    except Exception as e:
        print(f"\n✗ 실행 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 80)
    print(f"종료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)


if __name__ == "__main__":
    main()
