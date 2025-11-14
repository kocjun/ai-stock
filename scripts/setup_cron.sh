#!/bin/bash

##############################################################################
# cron job 자동 설정 스크립트
#
# 이 스크립트는 데이터 수집 자동화를 위한 cron job을 설정합니다.
##############################################################################

set -e

# 현재 디렉터리 절대 경로
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=================================================="
echo "AI 에이전트 데이터 수집 자동화 설정"
echo "=================================================="
echo ""

# 1. 현재 cron job 확인
echo "[1] 현재 cron job 확인"
echo "--------------------------------------------------"
if crontab -l 2>/dev/null | grep -q "ai-agent\|investment"; then
    echo "⚠️  이미 설정된 cron job이 있습니다:"
    crontab -l | grep -E "ai-agent|investment"
    echo ""
    read -p "기존 설정을 덮어쓸까요? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "설정을 취소합니다."
        exit 0
    fi
else
    echo "✓ 설정된 cron job이 없습니다."
fi

echo ""

# 2. 스크립트 실행 권한 확인
echo "[2] 스크립트 실행 권한 확인"
echo "--------------------------------------------------"
chmod +x "$SCRIPT_DIR/run_daily_collection.sh"
chmod +x "$SCRIPT_DIR/run_weekly_analysis.sh"
echo "✓ 실행 권한 설정 완료"

echo ""

# 3. cron job 추가
echo "[3] cron job 추가"
echo "--------------------------------------------------"

# 임시 cron 파일 생성
TEMP_CRON=$(mktemp)

# 기존 cron job 백업 (ai-agent 관련 제외)
crontab -l 2>/dev/null | grep -v "ai-agent\|investment" > "$TEMP_CRON" || true

# 새로운 cron job 추가
cat >> "$TEMP_CRON" << EOF

# ========================================
# AI 에이전트 데이터 수집 자동화
# ========================================

# 일간 데이터 수집: 매일 오후 6시 (18:00)
0 18 * * * cd $SCRIPT_DIR && ./run_daily_collection.sh >> $SCRIPT_DIR/logs/cron_daily.log 2>&1

# 주간 분석: 매주 토요일 오전 9시
0 9 * * 6 cd $SCRIPT_DIR && ./run_weekly_analysis.sh >> $SCRIPT_DIR/logs/cron_weekly.log 2>&1

EOF

# cron job 등록
crontab "$TEMP_CRON"
rm "$TEMP_CRON"

echo "✓ cron job 등록 완료"

echo ""

# 4. 등록 결과 확인
echo "[4] 등록된 cron job 확인"
echo "--------------------------------------------------"
crontab -l | grep -A 5 "AI 에이전트"

echo ""

# 5. 로그 디렉터리 생성
echo "[5] 로그 디렉터리 생성"
echo "--------------------------------------------------"
mkdir -p "$SCRIPT_DIR/logs"
mkdir -p "$SCRIPT_DIR/reports"
echo "✓ 디렉터리 생성 완료"

echo ""

# 6. 완료 안내
echo "=================================================="
echo "✅ 자동화 설정 완료!"
echo "=================================================="
echo ""
echo "📅 실행 스케줄:"
echo "  • 일간 데이터 수집: 매일 오후 6시 (18:00)"
echo "  • 주간 분석 리포트: 매주 토요일 오전 9시"
echo ""
echo "📁 로그 파일:"
echo "  • 일간: $SCRIPT_DIR/logs/cron_daily.log"
echo "  • 주간: $SCRIPT_DIR/logs/cron_weekly.log"
echo ""
echo "🔧 관리 명령어:"
echo "  • cron job 확인: crontab -l"
echo "  • cron job 편집: crontab -e"
echo "  • cron job 삭제: crontab -r"
echo "  • 로그 확인: tail -f logs/cron_daily.log"
echo ""
echo "💡 팁:"
echo "  • 수동 실행: ./run_daily_collection.sh"
echo "  • 즉시 테스트: 아래 명령어 실행"
echo "    cd $SCRIPT_DIR && ./run_daily_collection.sh"
echo ""
echo "=================================================="
