#!/bin/bash

##############################################################################
# Alert 자동화를 cron에 추가하는 스크립트
##############################################################################

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=================================================="
echo "Alert 자동화 cron job 추가"
echo "=================================================="
echo ""

# 임시 cron 파일
TEMP_CRON=$(mktemp)

# 기존 cron 복사
crontab -l 2>/dev/null > "$TEMP_CRON" || true

# 알림 cron이 이미 있는지 확인
if grep -q "run_alerts.sh" "$TEMP_CRON"; then
    echo "⚠️  알림 cron job이 이미 존재합니다."
    echo ""
    echo "현재 설정:"
    grep "run_alerts" "$TEMP_CRON"
    echo ""
    read -p "덮어쓸까요? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "취소되었습니다."
        rm "$TEMP_CRON"
        exit 0
    fi

    # 기존 알림 cron 제거
    grep -v "run_alerts" "$TEMP_CRON" > "${TEMP_CRON}.tmp"
    mv "${TEMP_CRON}.tmp" "$TEMP_CRON"
fi

# 새 알림 cron 추가
cat >> "$TEMP_CRON" << EOF

# 알림 체크: 장 시작 전 (오전 8시 30분)
30 8 * * 1-5 cd $SCRIPT_DIR && ./run_alerts.sh >> $SCRIPT_DIR/logs/cron_alerts.log 2>&1

# 알림 체크: 장 마감 후 (오후 4시)
0 16 * * 1-5 cd $SCRIPT_DIR && ./run_alerts.sh >> $SCRIPT_DIR/logs/cron_alerts.log 2>&1

EOF

# cron 등록
crontab "$TEMP_CRON"
rm "$TEMP_CRON"

echo "✅ 알림 cron job 추가 완료!"
echo ""
echo "📅 실행 스케줄:"
echo "  • 오전 8시 30분: 장 시작 전 알림 체크"
echo "  • 오후 4시: 장 마감 후 알림 체크"
echo ""
echo "🔍 등록된 cron job 확인:"
crontab -l | grep -E "알림|alert"
echo ""
echo "📁 로그 파일: $SCRIPT_DIR/logs/cron_alerts.log"
echo ""
echo "💡 수동 실행: ./run_alerts.sh"
echo "=================================================="
