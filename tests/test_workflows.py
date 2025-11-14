#!/usr/bin/env python3
"""n8n 워크플로우 테스트 스크립트"""

import os
import sys
from datetime import datetime

print("=" * 80)
print(" " * 25 + "n8n 워크플로우 테스트")
print("=" * 80)
print(f"실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

# 테스트할 에이전트 목록
agents = [
    ("1. Data Curator (데이터 수집)", "core.agents.investment_crew"),
    ("2. Screening Analyst (종목 스크리닝)", "core.agents.screening_crew"),
    ("3. Risk Manager (리스크 분석)", "core.agents.risk_crew"),
    ("4. Portfolio Planner (포트폴리오 최적화)", "core.agents.portfolio_crew"),
]

print("사용 가능한 워크플로우:")
for name, _ in agents:
    print(f"  {name}")
print()

# 사용자 선택
choice = input("테스트할 워크플로우 번호 (1-4, 또는 'all'): ").strip()

if choice == 'all':
    selected = agents
elif choice in ['1', '2', '3', '4']:
    selected = [agents[int(choice) - 1]]
else:
    print("❌ 잘못된 선택입니다.")
    sys.exit(1)

print()
print("=" * 80)
print("테스트 시작")
print("=" * 80)
print()

for name, module_path in selected:
    print(f"\n{'=' * 80}")
    print(f"🧪 테스트: {name}")
    print(f"{'=' * 80}\n")

    try:
        # 모듈 동적 임포트
        module_name = module_path.split('.')[-1]
        exec(f"from {module_path} import main")

        # main 함수 실행
        exec("main()")

        print(f"\n✅ {name} 완료\n")

    except Exception as e:
        print(f"\n❌ {name} 실패: {e}\n")
        import traceback
        traceback.print_exc()

print("\n" + "=" * 80)
print("테스트 완료")
print("=" * 80)
