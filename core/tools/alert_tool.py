"""
Alert Tool (CrewAI Tool)

가격 변동, 손절선/목표가, 리밸런싱 알림 도구
"""

from crewai.tools import BaseTool
from typing import Any
import sys
import os
import json

# 상위 디렉터리 모듈 import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from alert_manager import check_price_alerts, check_threshold_alerts, check_rebalance_alerts


class AlertTool(BaseTool):
    name: str = "alert_tool"
    description: str = """
    가격 변동, 손절선/목표가, 리밸런싱 알림 도구

    사용법:
    1. price:[임계값]
       - 가격 급락/급등 감지 (%, 기본값: 5%)
       - 예시: price:5.0 (5% 이상 변동 감지)

    2. threshold:[손절선],[목표가],[포트폴리오JSON]
       - 손절선/목표가 도달 체크
       - 포트폴리오 형식: [{"code":"005930","entry_price":70000,"quantity":10},...]
       - 예시: threshold:-10,20,[{"code":"005930","entry_price":70000,"quantity":10}]

    3. rebalance:[목표비중JSON],[현재포트폴리오JSON],[허용오차]
       - 리밸런싱 필요 여부 체크
       - 목표비중 형식: {"005930":0.3,"000660":0.2,...}
       - 현재포트폴리오 형식: [{"code":"005930","quantity":10,"value":700000},...]
       - 예시: rebalance:{"005930":0.5},[{"code":"005930","quantity":10,"value":700000}],0.05

    4. summary
       - 전체 알림 요약 (가격+손절선+리밸런싱)

    반환: 알림 리스트 (JSON 형식)
    """

    def _run(self, command: str) -> str:
        """
        알림 체크 실행

        Args:
            command: 명령어 문자열

        Returns:
            알림 결과 텍스트
        """
        try:
            parts = command.strip().split(':', 1)
            if len(parts) < 1:
                return "❌ 잘못된 명령어 형식입니다. 사용법을 확인하세요."

            cmd_type = parts[0].lower()

            # 1. 가격 알림
            if cmd_type == "price":
                threshold = 5.0
                if len(parts) > 1:
                    threshold = float(parts[1].strip())

                alerts = check_price_alerts(threshold=threshold, days=1)

                if len(alerts) == 0:
                    return f"✅ 가격 알림 없음 (임계값: ±{threshold}%)"

                # 결과 포맷
                summary = f"⚠️ 가격 급락/급등 감지 ({len(alerts)}건)\n\n"

                for i, alert in enumerate(alerts[:10], 1):
                    emoji = "📈" if alert['change_pct'] > 0 else "📉"
                    summary += f"{i}. {emoji} {alert['name']}({alert['code']})\n"
                    summary += f"   변동: {alert['change_pct']:+.2f}% "
                    summary += f"({alert['previous_price']:,.0f}원 → {alert['current_price']:,.0f}원)\n"
                    summary += f"   심각도: {alert['severity']}\n\n"

                if len(alerts) > 10:
                    summary += f"... 외 {len(alerts) - 10}건\n"

                return summary.strip()

            # 2. 손절선/목표가 알림
            elif cmd_type == "threshold":
                if len(parts) < 2:
                    return "❌ 형식: threshold:[손절선],[목표가],[포트폴리오JSON]"

                args = parts[1].split(',', 2)
                if len(args) < 3:
                    return "❌ 손절선, 목표가, 포트폴리오를 모두 입력하세요"

                stop_loss = float(args[0].strip())
                take_profit = float(args[1].strip())
                portfolio_json = args[2].strip()

                # JSON 파싱
                portfolio = json.loads(portfolio_json)

                alerts = check_threshold_alerts(
                    portfolio=portfolio,
                    stop_loss_pct=stop_loss,
                    take_profit_pct=take_profit
                )

                if len(alerts) == 0:
                    return f"✅ 손절선/목표가 알림 없음 (손절: {stop_loss}%, 목표: {take_profit}%)"

                # 결과 포맷
                summary = f"⚠️ 손절선/목표가 알림 ({len(alerts)}건)\n\n"

                for i, alert in enumerate(alerts, 1):
                    if alert['type'] == 'stop_loss':
                        emoji = "🚨"
                        label = "손절선"
                    else:
                        emoji = "🎯"
                        label = "목표가"

                    summary += f"{i}. {emoji} {label} 도달: {alert['name']}({alert['code']})\n"
                    summary += f"   진입가: {alert['entry_price']:,.0f}원\n"
                    summary += f"   현재가: {alert['current_price']:,.0f}원\n"
                    summary += f"   수익률: {alert['return_pct']:+.2f}%\n"
                    summary += f"   보유량: {alert['quantity']}주\n\n"

                return summary.strip()

            # 3. 리밸런싱 알림
            elif cmd_type == "rebalance":
                if len(parts) < 2:
                    return "❌ 형식: rebalance:[목표비중JSON],[현재포트폴리오JSON],[허용오차]"

                args = parts[1].split(',', 2)
                if len(args) < 2:
                    return "❌ 목표비중과 현재포트폴리오를 모두 입력하세요"

                # 목표 비중 파싱
                target_weights = json.loads(args[0].strip())

                # 현재 포트폴리오 파싱
                portfolio = json.loads(args[1].strip())

                # 허용 오차 (기본값: 5%p)
                threshold = 0.05
                if len(args) > 2:
                    threshold = float(args[2].strip())

                alerts = check_rebalance_alerts(
                    portfolio=portfolio,
                    target_weights=target_weights,
                    threshold=threshold
                )

                if len(alerts) == 0:
                    return f"✅ 리밸런싱 불필요 (허용오차: {threshold*100}%p)"

                # 결과 포맷
                summary = f"🔄 리밸런싱 필요\n\n"

                for alert in alerts:
                    summary += f"포트폴리오 총액: {alert['total_value']:,.0f}원\n"
                    summary += f"조정 필요 종목: {len(alert['rebalance_list'])}개\n\n"

                    for i, item in enumerate(alert['rebalance_list'], 1):
                        summary += f"{i}. {item['name']}({item['code']})\n"
                        summary += f"   현재 비중: {item['current_weight']:.2f}%\n"
                        summary += f"   목표 비중: {item['target_weight']:.2f}%\n"
                        summary += f"   차이: {item['diff']:.2f}%p\n"
                        summary += f"   권장: {item['action']}\n\n"

                return summary.strip()

            # 4. 전체 요약
            elif cmd_type == "summary":
                summary = "📊 알림 종합 요약\n\n"

                # 가격 알림
                price_alerts = check_price_alerts(threshold=5.0, days=1)
                summary += f"1️⃣ 가격 급락/급등: {len(price_alerts)}건\n"
                if len(price_alerts) > 0:
                    for alert in price_alerts[:3]:
                        summary += f"   • {alert['message']}\n"

                summary += "\n"

                # 손절선/목표가는 포트폴리오 정보 필요하므로 생략
                summary += "2️⃣ 손절선/목표가: 포트폴리오 정보 필요\n"
                summary += "3️⃣ 리밸런싱: 포트폴리오 정보 필요\n\n"

                summary += "💡 상세 알림은 각 명령어를 개별 실행하세요."

                return summary.strip()

            else:
                return f"❌ 알 수 없는 명령어: {cmd_type}"

        except json.JSONDecodeError as e:
            return f"❌ JSON 파싱 오류: {str(e)}"
        except ValueError as e:
            return f"❌ 잘못된 입력값: {str(e)}"
        except Exception as e:
            return f"❌ 알림 체크 중 오류: {str(e)}"


if __name__ == "__main__":
    """도구 테스트"""
    print("AlertTool 테스트\n")

    tool = AlertTool()

    # 테스트 1: 가격 알림
    print("테스트 1: 가격 급락/급등 감지 (5% 이상)")
    print("-" * 60)
    result = tool.run("price:5.0")
    print(result)

    print("\n" + "="*60 + "\n")

    # 테스트 2: 손절선/목표가
    print("테스트 2: 손절선/목표가 체크")
    print("-" * 60)

    # 샘플 포트폴리오
    portfolio = [
        {"code": "005930", "entry_price": 70000, "quantity": 10},
        {"code": "000660", "entry_price": 130000, "quantity": 5}
    ]
    portfolio_json = json.dumps(portfolio)

    result = tool.run(f"threshold:-10,20,{portfolio_json}")
    print(result)

    print("\n" + "="*60 + "\n")

    # 테스트 3: 전체 요약
    print("테스트 3: 전체 알림 요약")
    print("-" * 60)
    result = tool.run("summary")
    print(result)
