#!/bin/bash
# 모든 워크플로우 순차 테스트 스크립트

set -e

echo "=================================="
echo "워크플로우 테스트 시작"
echo "=================================="
echo ""

# 가상환경 활성화
source .venv/bin/activate

# 1. Data Curator (데이터 수집)
echo "1️⃣ Data Curator 테스트..."
echo "----------------------------------"
python core/agents/investment_crew.py
echo ""
echo "✅ Data Curator 완료"
echo ""

# 2. Screening Analyst (종목 스크리닝)
echo "2️⃣ Screening Analyst 테스트..."
echo "----------------------------------"
python core/agents/screening_crew.py
echo ""
echo "✅ Screening Analyst 완료"
echo ""

# 3. Risk Manager (리스크 분석)
echo "3️⃣ Risk Manager 테스트..."
echo "----------------------------------"
python core/agents/risk_crew.py
echo ""
echo "✅ Risk Manager 완료"
echo ""

# 4. Portfolio Planner (포트폴리오 최적화)
echo "4️⃣ Portfolio Planner 테스트..."
echo "----------------------------------"
python core/agents/portfolio_crew.py
echo ""
echo "✅ Portfolio Planner 완료"
echo ""

# 5. 통합 워크플로우
echo "5️⃣ 통합 워크플로우 테스트..."
echo "----------------------------------"
python core/agents/integrated_crew.py
echo ""
echo "✅ 통합 워크플로우 완료"
echo ""

echo "=================================="
echo "✅ 모든 워크플로우 테스트 완료!"
echo "=================================="
