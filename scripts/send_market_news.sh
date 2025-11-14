#!/bin/bash

##############################################
# 시장 뉴스 분석 및 이메일 발송 스크립트
##############################################

set -e  # 에러 발생 시 중단

# 설정
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_DIR="${PROJECT_ROOT}/logs"
LOG_FILE="${LOG_DIR}/market_news_$(date +%Y%m%d_%H%M%S).log"

# 로그 디렉터리 생성
mkdir -p "${LOG_DIR}"

# 로그 함수
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "${LOG_FILE}"
}

log "============================================"
log "시장 뉴스 분석 및 이메일 발송"
log "============================================"

# 0. .env 파일 로드
log ""
log "0. 환경 설정 파일 로드"
log "-------------------------------------------"

if [ -f "${PROJECT_ROOT}/.env" ]; then
    log "✅ .env 파일 발견, 환경 변수 로드"
    # .env 파일에서 변수 로드 (# 주석, 빈 줄 제외)
    set -a
    while IFS= read -r line; do
        # 주석과 빈 줄 제외
        [[ "$line" =~ ^#.*$ ]] && continue
        [[ -z "$line" ]] && continue
        # 따옴표 제거 (KEY="value" → KEY=value)
        line=${line//\"/}
        export "$line"
    done < "${PROJECT_ROOT}/.env"
    set +a
else
    log "⚠️  .env 파일 없음"
fi

# 1. 환경 체크
log ""
log "1. 환경 체크"
log "-------------------------------------------"

if [ ! -d "${PROJECT_ROOT}/.venv" ]; then
    log "❌ 가상환경이 없습니다."
    exit 1
fi
log "✅ 가상환경 확인됨"

# 2. 가상환경 활성화
log ""
log "2. Python 가상환경 활성화"
log "-------------------------------------------"
cd "${PROJECT_ROOT}"
source .venv/bin/activate
log "✅ 가상환경 활성화 완료"

# 3. 환경 변수 확인
log ""
log "3. SMTP 환경 변수 확인"
log "-------------------------------------------"

if [ -z "$SMTP_SERVER" ]; then
    log "⚠️  SMTP_SERVER이 설정되지 않았습니다"
else
    log "✅ SMTP_SERVER 설정됨: $SMTP_SERVER"
fi

if [ -z "$EMAIL_FROM" ] && [ -z "$EMAIL_FROM_ADDRESS" ]; then
    log "⚠️  EMAIL_FROM 또는 EMAIL_FROM_ADDRESS가 설정되지 않았습니다"
else
    log "✅ 발송자 이메일 설정됨"
fi

if [ -z "$REPORT_EMAIL_RECIPIENT" ] && [ -z "$EMAIL_TO" ]; then
    log "⚠️  REPORT_EMAIL_RECIPIENT 또는 EMAIL_TO가 설정되지 않았습니다"
else
    log "✅ 수신자 이메일 설정됨"
fi

if [ -z "$SMTP_PASSWORD" ]; then
    log "⚠️  SMTP_PASSWORD가 설정되지 않았습니다 (이메일 발송 불가)"
else
    log "✅ SMTP_PASSWORD 설정됨"
fi

# 4. 시장 뉴스 분석 및 이메일 발송 실행
log ""
log "4. 시장 뉴스 분석 및 이메일 발송 실행"
log "-------------------------------------------"

if python core/agents/market_news_crew.py >> "${LOG_FILE}" 2>&1; then
    log "✅ 뉴스 분석 및 이메일 발송 완료"
    EXIT_CODE=0
else
    log "❌ 뉴스 분석 실패"
    EXIT_CODE=1
fi

# 5. 완료
log ""
log "============================================"
if [ $EXIT_CODE -eq 0 ]; then
    log "✅ 시장 뉴스 분석 완료"
else
    log "❌ 시장 뉴스 분석 실패"
fi
log "로그 파일: ${LOG_FILE}"
log "============================================"

exit $EXIT_CODE
