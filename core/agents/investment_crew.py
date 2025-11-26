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
from core.utils.db_utils import get_db_connection

load_dotenv()


def summarize_data_state() -> dict:
    """현재 stocks/prices 상태 요약"""
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM stocks;")
        stock_count = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*), COUNT(DISTINCT code), MAX(date) FROM prices;")
        price_count, distinct_codes, latest_date = cur.fetchone()

        return {
            "stocks": stock_count,
            "price_rows": price_count or 0,
            "price_codes": distinct_codes or 0,
            "latest_price_date": latest_date
        }


def print_data_summary(label: str, summary: dict):
    print(f"\n[{label}] 데이터 상태 요약")
    print(f"  - 종목 수: {summary['stocks']}")
    print(f"  - 가격 데이터 행수: {summary['price_rows']}")
    print(f"  - 가격 데이터 보유 종목 수: {summary['price_codes']}")
    latest_date = summary['latest_price_date']
    latest_str = latest_date.strftime('%Y-%m-%d') if latest_date else '없음'
    print(f"  - 가격 데이터 최신 일자: {latest_str}\n")


def decide_collection_profile(summary: dict) -> dict:
    """요일/커버리지 기반 수집 전략 결정"""
    weekday = datetime.now().weekday()  # 0=Mon
    age_days = 0
    if summary["latest_price_date"]:
        age_days = (datetime.utcnow().date() - summary["latest_price_date"]).days

    profiles = [
        {
            "name": "대형주 집중",
            "market": "KOSPI",
            "limit": 70,
            "days": 30,
            "description": "시가총액 상위 대형주 업데이트",
            "when": lambda wd, age: wd in (0, 3)  # Mon/Wed
        },
        {
            "name": "테크·성장주",
            "market": "KOSDAQ",
            "limit": 80,
            "days": 25,
            "description": "성장 섹터(KOSDAQ) 수집",
            "when": lambda wd, age: wd in (1, 4)  # Tue/Fri
        },
        {
            "name": "단기 변동성",
            "market": "KOSPI",
            "limit": 40,
            "days": 15,
            "description": "단기 급등/급락 종목 모니터링",
            "when": lambda wd, age: wd == 2  # Wed
        },
        {
            "name": "주말 리프레시",
            "market": "KOSPI",
            "limit": 50,
            "days": 45,
            "description": "주말 리프레시",
            "when": lambda wd, age: wd >= 5  # Sat/Sun
        }
    ]

    # 커버리지 부족/최신일자 오래됨이면 강제 기본 수집
    if summary["price_rows"] < summary["stocks"] * 15 or age_days > 2:
        return {
            "name": "기본 커버리지",
            "market": "KOSPI",
            "limit": 80,
            "days": 45,
            "description": "커버리지 보충 수집"
        }

    for profile in profiles:
        if profile["when"](weekday, age_days):
            return profile

    return profiles[0]


def build_data_curator_crew(
    market: str = "KOSPI",
    limit: int = 50,
    days: int = 30,
    baseline_state: dict | None = None,
    strategy_name: str = ""
):
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

    baseline_text = ""
    if baseline_state:
        latest = baseline_state["latest_price_date"]
        latest_str = latest.strftime('%Y-%m-%d') if latest else "없음"
        baseline_text = (
            f"현재 DB 상태 요약: 종목 {baseline_state['stocks']}개, "
            f"가격 데이터 {baseline_state['price_rows']} rows, "
            f"가격 데이터 최신 일자 {latest_str}."
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
        - {baseline_text or "실행 전 상태 대비 변화(신규 종목/가격 행수 증가량)를 정량적으로 명시하세요."}
        - 이번 전략: {strategy_name or "기본"} — 전략 의도에 맞는 종목 특징을 언급하세요.
        """,
        expected_output=f"""
        데이터 수집 결과 리포트:
        - 수집된 종목 수: N개
        - 수집된 가격 데이터: N rows
        - 성공/실패 건수
        - 수집 기간 정보
        - 이전 상태 대비 증가/감소 요약
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
        - 최근 실행 전 상태({baseline_text or "상세는 collection_task 참고"})와 비교하여 품질의 변화(커버리지 개선/악화, 날짜 지연)를 반드시 언급하세요.
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
        - 실행 전 상태 대비 이번 수집이 가져온 개선 사항과 남은 리스크를 명확히 대조하세요.
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
    before_state = summarize_data_state()

    print("=" * 80)
    print(" " * 25 + "한국 주식 투자 분석 AI 에이전트")
    print(" " * 30 + "Data Curator Phase")
    print("=" * 80)
    print(f"실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Ollama 서버 확인
    ollama_url = os.getenv("OPENAI_API_BASE", "http://127.0.0.1:11434")
    print(f"Ollama 서버: {ollama_url}")
    print(f"모델: {os.getenv('OPENAI_MODEL_NAME', 'llama3.1:8b')}\n")

    profile = decide_collection_profile(before_state)
    MARKET = profile["market"]
    LIMIT = profile["limit"]
    DAYS = profile["days"]

    print(f"수집 설정:")
    print(f"  - 전략: {profile['name']} ({profile['description']})")
    print(f"  - 시장: {MARKET}")
    print(f"  - 종목 수: {LIMIT}")
    print(f"  - 기간: 최근 {DAYS}일\n")
    print("=" * 80)
    print_data_summary("실행 전", before_state)

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

        after_state = summarize_data_state()
        print_data_summary("실행 후", after_state)

        delta_stocks = after_state['stocks'] - before_state['stocks']
        delta_rows = after_state['price_rows'] - before_state['price_rows']
        if delta_rows <= 0:
            print("[경고] 가격 데이터 행수가 증가하지 않았습니다. 수집 결과를 확인하세요.")
        else:
            print(f"[정보] 가격 데이터가 {delta_rows:,}건 증가했습니다.")

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
