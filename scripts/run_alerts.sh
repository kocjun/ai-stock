#!/bin/bash

##############################################################################
# 알림 자동 실행 스크립트
#
# Alert Manager를 실행하고 중요한 알림이 있으면 로그에 저장합니다.
##############################################################################

set -e

# 설정
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="${SCRIPT_DIR}/logs"
LOG_FILE="${LOG_DIR}/alerts_$(date +%Y%m%d_%H%M%S).log"

# 로그 디렉터리 생성
mkdir -p "${LOG_DIR}"

# 로그 함수
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "${LOG_FILE}"
}

log "============================================"
log "Alert Manager 실행"
log "============================================"

# 가상환경 활성화
cd "${SCRIPT_DIR}"
source .venv/bin/activate

# Alert Manager 실행
log "알림 체크 중..."
python alert_manager.py >> "${LOG_FILE}" 2>&1

# 알림 개수 확인
ALERT_COUNT=$(grep -c "알림 발견" "${LOG_FILE}" || echo "0")

if [ "$ALERT_COUNT" -gt 0 ]; then
    log "✅ ${ALERT_COUNT}개 알림 발견!"
    log "로그 파일: ${LOG_FILE}"

    # 중요 알림만 추출
    log ""
    log "=== 주요 알림 ==="
    grep -E "급락|급등|손절|목표" "${LOG_FILE}" | head -10
else
    log "알림 없음"
fi

log "============================================"
log "완료"
log "============================================"

exit 0
