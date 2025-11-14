#!/bin/bash

##############################################
# 한국 주식 데이터 일간 수집 자동화 스크립트
##############################################

set -e  # 에러 발생 시 중단

# 설정
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
LOG_DIR="${SCRIPT_DIR}/logs"
LOG_FILE="${LOG_DIR}/collection_$(date +%Y%m%d_%H%M%S).log"

# 환경 변수 로드 (.env가 있으면)
if [ -f "${PROJECT_ROOT}/.env" ]; then
    set -a
    # shellcheck disable=SC1090
    source "${PROJECT_ROOT}/.env"
    set +a
fi

LLM_BASE_URL="${OPENAI_API_BASE:-http://127.0.0.1:11434}"

# 로그 디렉터리 생성
mkdir -p "${LOG_DIR}"

# 로그 함수
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "${LOG_FILE}"
}

log "============================================"
log "한국 주식 데이터 일간 수집 시작"
log "============================================"

# 1. 환경 체크
log "1. 환경 체크"
log "-------------------------------------------"

# Docker 서비스 확인
if ! docker ps | grep -q "investment_postgres"; then
    log "✗ PostgreSQL 컨테이너가 실행 중이 아닙니다."
    log "docker-compose up -d 를 실행하세요."
    exit 1
fi
log "✓ PostgreSQL 컨테이너 실행 중"

# Ollama 서버 확인
if ! curl -s "${LLM_BASE_URL}/api/tags" > /dev/null; then
    log "✗ Ollama 서버에 연결할 수 없습니다."
    log "서버 주소: ${LLM_BASE_URL}"
    log "ollama serve 를 실행하거나 네트워크 설정을 확인하세요."
    exit 1
fi
log "✓ Ollama 서버 연결 성공"

# 2. 가상환경 활성화
log ""
log "2. Python 가상환경 활성화"
log "-------------------------------------------"
cd "${SCRIPT_DIR}"
if [ ! -d ".venv" ]; then
    log "✗ 가상환경이 없습니다. 먼저 python3 -m venv .venv 를 실행하세요."
    exit 1
fi

source .venv/bin/activate
log "✓ 가상환경 활성화 완료"

# 3. CrewAI 실행
log ""
log "3. CrewAI Data Curator 실행"
log "-------------------------------------------"

if python investment_crew.py >> "${LOG_FILE}" 2>&1; then
    log "✓ 데이터 수집 성공"
    EXIT_CODE=0
else
    log "✗ 데이터 수집 실패 (종료 코드: $?)"
    EXIT_CODE=1
fi

# 4. 결과 확인
log ""
log "4. 데이터베이스 확인"
log "-------------------------------------------"

STOCK_COUNT=$(docker exec investment_postgres psql -U invest_user -d investment_db -t -c "SELECT COUNT(*) FROM stocks;" | xargs)
PRICE_COUNT=$(docker exec investment_postgres psql -U invest_user -d investment_db -t -c "SELECT COUNT(*) FROM prices;" | xargs)
LOG_COUNT=$(docker exec investment_postgres psql -U invest_user -d investment_db -t -c "SELECT COUNT(*) FROM data_collection_logs;" | xargs)

log "종목 수: ${STOCK_COUNT}"
log "가격 데이터: ${PRICE_COUNT} rows"
log "수집 로그: ${LOG_COUNT} 건"

# 5. 완료
log ""
log "============================================"
log "일간 수집 완료"
log "로그 파일: ${LOG_FILE}"
log "============================================"

exit ${EXIT_CODE}
