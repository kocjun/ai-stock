"""
Alert Manager 에이전트

가격 변동, 손절선/목표가, 리밸런싱 시점 알림
"""

from crewai import Agent, Task, Crew, Process
from core.tools.data_collection_tool import DataCollectionTool
from core.tools.n8n_webhook_tool import N8nWebhookTool
from core.utils.llm_utils import build_llm, get_llm_mode
from dotenv import load_dotenv
import os
import pandas as pd
from datetime import datetime, timedelta
from db_utils import get_db_connection
from typing import Dict, List, Optional

# 환경 변수 로드
load_dotenv()


def check_price_alerts(threshold: float = 5.0, days: int = 1) -> List[Dict]:
    """
    가격 급락/급등 감지

    Args:
        threshold: 임계값 (%, 기본값: 5%)
        days: 비교 기간 (일, 기본값: 1일)

    Returns:
        알림 리스트
    """
    conn = get_db_connection()
    alerts = []

    try:
        # 최근 N일 가격 데이터 조회
        query = """
            WITH latest AS (
                SELECT code, date, close,
                       ROW_NUMBER() OVER (PARTITION BY code ORDER BY date DESC) as rn
                FROM prices
            ),
            price_change AS (
                SELECT
                    l1.code,
                    s.name,
                    l1.close as current_price,
                    l2.close as previous_price,
                    ((l1.close - l2.close) / l2.close * 100) as change_pct,
                    l1.date as current_date,
                    l2.date as previous_date
                FROM latest l1
                JOIN latest l2 ON l1.code = l2.code AND l2.rn = l1.rn + %s
                JOIN stocks s ON l1.code = s.code
                WHERE l1.rn = 1
            )
            SELECT *
            FROM price_change
            WHERE ABS(change_pct) >= %s
            ORDER BY ABS(change_pct) DESC
            LIMIT 20
        """

        df = pd.read_sql(query, conn, params=(days, threshold))

        for _, row in df.iterrows():
            alert_type = "급등" if row['change_pct'] > 0 else "급락"
            severity = "높음" if abs(row['change_pct']) >= 10 else "보통"

            alerts.append({
                'type': 'price_change',
                'severity': severity,
                'alert_type': alert_type,
                'code': row['code'],
                'name': row['name'],
                'current_price': float(row['current_price']),
                'previous_price': float(row['previous_price']),
                'change_pct': float(row['change_pct']),
                'current_date': str(row['current_date']),
                'previous_date': str(row['previous_date']),
                'message': f"{row['name']}({row['code']}) {alert_type} 감지: {row['change_pct']:+.2f}%"
            })

    finally:
        conn.close()

    return alerts


def check_threshold_alerts(
    portfolio: List[Dict[str, any]],
    stop_loss_pct: float = -10.0,
    take_profit_pct: float = 20.0
) -> List[Dict]:
    """
    손절선/목표가 알림

    Args:
        portfolio: 포트폴리오 [{code, entry_price, quantity}, ...]
        stop_loss_pct: 손절선 (%, 기본값: -10%)
        take_profit_pct: 목표가 (%, 기본값: +20%)

    Returns:
        알림 리스트
    """
    if len(portfolio) == 0:
        return []

    conn = get_db_connection()
    alerts = []

    try:
        for position in portfolio:
            code = position['code']
            entry_price = position['entry_price']
            quantity = position.get('quantity', 0)

            # 최신 가격 조회
            query = """
                SELECT close, date
                FROM prices
                WHERE code = %s
                ORDER BY date DESC
                LIMIT 1
            """
            result = pd.read_sql(query, conn, params=(code,))

            if len(result) == 0:
                continue

            current_price = float(result['close'].iloc[0])
            current_date = str(result['date'].iloc[0])

            # 수익률 계산
            return_pct = ((current_price - entry_price) / entry_price) * 100

            # 종목 정보
            stock_query = "SELECT name FROM stocks WHERE code = %s"
            stock_result = pd.read_sql(stock_query, conn, params=(code,))
            name = stock_result['name'].iloc[0] if len(stock_result) > 0 else code

            # 손절선 체크
            if return_pct <= stop_loss_pct:
                alerts.append({
                    'type': 'stop_loss',
                    'severity': '높음',
                    'code': code,
                    'name': name,
                    'entry_price': entry_price,
                    'current_price': current_price,
                    'return_pct': return_pct,
                    'threshold': stop_loss_pct,
                    'quantity': quantity,
                    'date': current_date,
                    'message': f"⚠️ 손절선 도달: {name}({code}) {return_pct:.2f}% (목표: {stop_loss_pct}%)"
                })

            # 목표가 체크
            elif return_pct >= take_profit_pct:
                alerts.append({
                    'type': 'take_profit',
                    'severity': '보통',
                    'code': code,
                    'name': name,
                    'entry_price': entry_price,
                    'current_price': current_price,
                    'return_pct': return_pct,
                    'threshold': take_profit_pct,
                    'quantity': quantity,
                    'date': current_date,
                    'message': f"🎯 목표가 도달: {name}({code}) {return_pct:+.2f}% (목표: {take_profit_pct}%)"
                })

    finally:
        conn.close()

    return alerts


def check_rebalance_alerts(
    portfolio: List[Dict[str, any]],
    target_weights: Dict[str, float],
    threshold: float = 0.05
) -> List[Dict]:
    """
    리밸런싱 알림

    Args:
        portfolio: 현재 포트폴리오 [{code, quantity, value}, ...]
        target_weights: 목표 비중 {code: weight}
        threshold: 허용 오차 (기본값: 5%p)

    Returns:
        알림 리스트
    """
    if len(portfolio) == 0:
        return []

    alerts = []

    # 전체 포트폴리오 가치 계산
    total_value = sum(p['value'] for p in portfolio)

    if total_value == 0:
        return []

    # 현재 비중 계산
    current_weights = {}
    for position in portfolio:
        code = position['code']
        current_weights[code] = position['value'] / total_value

    # 목표 비중과 비교
    rebalance_needed = []

    for code, target_weight in target_weights.items():
        current_weight = current_weights.get(code, 0)
        weight_diff = abs(current_weight - target_weight)

        if weight_diff > threshold:
            # 종목 정보
            conn = get_db_connection()
            try:
                query = "SELECT name FROM stocks WHERE code = %s"
                result = pd.read_sql(query, conn, params=(code,))
                name = result['name'].iloc[0] if len(result) > 0 else code
            finally:
                conn.close()

            action = "매수" if current_weight < target_weight else "매도"
            rebalance_needed.append({
                'code': code,
                'name': name,
                'current_weight': current_weight * 100,
                'target_weight': target_weight * 100,
                'diff': weight_diff * 100,
                'action': action
            })

    if len(rebalance_needed) > 0:
        alerts.append({
            'type': 'rebalance',
            'severity': '보통',
            'message': f"리밸런싱 필요: {len(rebalance_needed)}개 종목",
            'rebalance_list': rebalance_needed,
            'total_value': total_value
        })

    return alerts


def create_alert_manager_crew(
    mode: str = "price",
    threshold: float = 5.0,
    portfolio: Optional[List[Dict]] = None
):
    """
    Alert Manager Crew 생성

    Args:
        mode: 알림 모드 (price, threshold, rebalance)
        threshold: 임계값
        portfolio: 포트폴리오 정보

    Returns:
        Crew 객체
    """
    llm = build_llm(mode=get_llm_mode())

    # 도구 초기화
    data_tool = DataCollectionTool()
    webhook_tool = N8nWebhookTool(webhook_url=os.getenv("N8N_WEBHOOK_URL"))

    # Alert Manager 에이전트
    alert_manager = Agent(
        role="Alert Manager",
        goal="시장 상황을 모니터링하고 중요한 이벤트를 알립니다",
        backstory="금융 시장 모니터링 전문가로 15년 경력. 리스크 관리와 적시 알림을 최우선으로 합니다.",
        llm=llm,
        tools=[data_tool, webhook_tool],
        verbose=True,
        allow_delegation=False
    )

    # 태스크 정의
    if mode == "price":
        task_description = f"""
        최근 가격 변동을 모니터링하고 {threshold}% 이상 급락/급등한 종목을 찾아서 알림을 생성하세요.

        다음 정보를 포함해야 합니다:
        - 종목명 및 코드
        - 변동 폭 (%)
        - 현재 가격 vs 이전 가격
        - 심각도 (높음/보통)
        """
        expected_output = "가격 급락/급등 알림 리스트"

    elif mode == "threshold":
        task_description = """
        포트폴리오 내 종목들의 손절선/목표가 도달 여부를 확인하세요.

        다음 정보를 포함해야 합니다:
        - 손절선 도달 종목 (우선순위 높음)
        - 목표가 도달 종목
        - 수익률 및 권장 조치
        """
        expected_output = "손절선/목표가 알림 리스트"

    else:  # rebalance
        task_description = f"""
        포트폴리오 비중을 확인하고 목표 비중에서 {threshold*100}%p 이상 이탈한 종목을 찾으세요.

        다음 정보를 포함해야 합니다:
        - 현재 비중 vs 목표 비중
        - 권장 조치 (매수/매도)
        - 리밸런싱 우선순위
        """
        expected_output = "리밸런싱 알림 리스트"

    alert_task = Task(
        description=task_description,
        expected_output=expected_output,
        agent=alert_manager
    )

    # Crew 생성
    crew = Crew(
        agents=[alert_manager],
        tasks=[alert_task],
        process=Process.sequential,
        verbose=True
    )

    return crew


if __name__ == "__main__":
    """테스트 실행"""
    print("\n" + "="*60)
    print("Alert Manager 테스트")
    print("="*60 + "\n")

    # 테스트 1: 가격 알림
    print("테스트 1: 가격 급락/급등 감지 (±5% 이상)")
    print("-" * 60)
    price_alerts = check_price_alerts(threshold=5.0, days=1)

    if len(price_alerts) > 0:
        print(f"\n✅ {len(price_alerts)}개 알림 발견\n")
        for alert in price_alerts[:5]:
            print(f"  {alert['message']}")
    else:
        print("\n알림 없음")

    # 테스트 2: 손절선/목표가 (샘플 포트폴리오)
    print("\n" + "="*60)
    print("테스트 2: 손절선/목표가 체크")
    print("-" * 60)

    # 샘플 포트폴리오
    sample_portfolio = [
        {'code': '005930', 'entry_price': 70000, 'quantity': 10},
        {'code': '000660', 'entry_price': 130000, 'quantity': 5},
    ]

    threshold_alerts = check_threshold_alerts(
        portfolio=sample_portfolio,
        stop_loss_pct=-10.0,
        take_profit_pct=20.0
    )

    if len(threshold_alerts) > 0:
        print(f"\n✅ {len(threshold_alerts)}개 알림 발견\n")
        for alert in threshold_alerts:
            print(f"  {alert['message']}")
    else:
        print("\n알림 없음")

    print("\n" + "="*60)
    print("Alert Manager 테스트 완료")
    print("="*60)
