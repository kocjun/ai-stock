#!/bin/bash

echo "🧪 시스템 모니터 테스트 시작..."
echo ""

# 테스트 1: 상태 확인
echo "✅ Test 1: 상태 확인"
python3 system_monitor.py status | head -20
echo ""

# 테스트 2: 헬스 체크
echo "✅ Test 2: 헬스 체크"
python3 system_monitor.py health 2>&1 | tail -5
echo ""

# 테스트 3: 파일 구조 확인
echo "✅ Test 3: 파일 구조"
ls -lh system_monitor.py monitor.sh processes.json monitor.log 2>/dev/null | awk '{print $9, "-", $5}'
echo ""

echo "🎉 모든 테스트 완료!"
