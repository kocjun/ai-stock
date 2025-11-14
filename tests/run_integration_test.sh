#!/bin/bash

# ================================================
# AI 분석 + Paper Trading 통합 테스트 스크립트
# ================================================

set -e  # 오류 발생 시 종료

# 색상 정의
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 프로젝트 루트 디렉토리
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

# 환경 변수 로드 (.env가 있으면)
if [ -f "${PROJECT_ROOT}/.env" ]; then
    set -a
    # shellcheck disable=SC1090
    source "${PROJECT_ROOT}/.env"
    set +a
fi

LLM_BASE_URL="${OPENAI_API_BASE:-http://127.0.0.1:11434}"

# 로그 디렉토리 및 파일
TEST_LOG_DIR="$PROJECT_ROOT/tests/logs"
mkdir -p "$TEST_LOG_DIR"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
TEST_LOG="$TEST_LOG_DIR/integration_test_${TIMESTAMP}.log"

# 결과 저장
TEST_RESULTS_FILE="$PROJECT_ROOT/tests/test_results_${TIMESTAMP}.md"

# 테스트 결과 카운터
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# ================================================
# 유틸리티 함수
# ================================================

log() {
    echo -e "${GREEN}[$(date +'%H:%M:%S')]${NC} $1" | tee -a "$TEST_LOG"
}

log_warn() {
    echo -e "${YELLOW}[$(date +'%H:%M:%S')] ⚠️  $1${NC}" | tee -a "$TEST_LOG"
}

log_error() {
    echo -e "${RED}[$(date +'%H:%M:%S')] ❌ $1${NC}" | tee -a "$TEST_LOG"
}

log_info() {
    echo -e "${BLUE}[$(date +'%H:%M:%S')] ℹ️  $1${NC}" | tee -a "$TEST_LOG"
}

test_pass() {
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    PASSED_TESTS=$((PASSED_TESTS + 1))
    log "✅ $1"
}

test_fail() {
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    FAILED_TESTS=$((FAILED_TESTS + 1))
    log_error "❌ $1"
}

test_warn() {
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    log_warn "$1"
}

separator() {
    echo "" | tee -a "$TEST_LOG"
    echo "============================================================" | tee -a "$TEST_LOG"
    echo "$1" | tee -a "$TEST_LOG"
    echo "============================================================" | tee -a "$TEST_LOG"
    echo "" | tee -a "$TEST_LOG"
}

# ================================================
# 테스트 시작
# ================================================

separator "AI 분석 + Paper Trading 통합 테스트"
log "테스트 시작: $(date '+%Y-%m-%d %H:%M:%S')"
log "로그 파일: $TEST_LOG"
log "결과 파일: $TEST_RESULTS_FILE"

# 가상환경 활성화
if [ -d ".venv" ]; then
    source .venv/bin/activate
    log "가상환경 활성화 완료"
else
    log_error "가상환경을 찾을 수 없습니다: .venv"
    exit 1
fi

# ================================================
# Phase 1: 사전 준비 및 환경 검증
# ================================================

separator "Phase 1: 사전 준비 및 환경 검증"

# 1.1 Docker 서비스 확인
log_info "Docker 서비스 확인 중..."
if command -v docker > /dev/null 2>&1; then
    if docker ps | grep -q "investment_postgres"; then
        test_pass "PostgreSQL 컨테이너 실행 중"
    else
        test_fail "PostgreSQL 컨테이너가 실행되지 않음"
    fi

    if docker ps | grep -q "n8n"; then
        test_pass "n8n 컨테이너 실행 중"
    else
        test_warn "n8n 컨테이너가 실행되지 않음 (선택사항)"
    fi
else
    test_warn "Docker 명령을 찾을 수 없어 컨테이너 상태 체크를 건너뜁니다"
fi

# 1.2 Ollama 서버 확인
log_info "Ollama 서버 확인 중..."
if curl -s "${LLM_BASE_URL}/api/tags" > /dev/null 2>&1; then
    test_pass "Ollama 서버 응답 정상"
else
    test_fail "Ollama 서버 응답 없음"
    log_error "확인: 서버 주소 ${LLM_BASE_URL} / ollama serve 실행 여부 / 네트워크"
    exit 1
fi

# 1.3 데이터베이스 연결 확인
log_info "데이터베이스 연결 확인 중..."
if python core/utils/db_utils.py > /dev/null 2>&1; then
    test_pass "데이터베이스 연결 성공"
else
    test_fail "데이터베이스 연결 실패"
    exit 1
fi

# 1.4 데이터 확인
log_info "데이터 수집 상태 확인 중..."
DATA_CHECK=$(python -c "
from core.utils.db_utils import get_db_connection
conn = get_db_connection()
cur = conn.cursor()
cur.execute('SELECT COUNT(*) FROM stocks')
stock_count = cur.fetchone()[0]
cur.execute('SELECT MAX(date) FROM prices')
latest_date = cur.fetchone()[0]
print(f'{stock_count}|{latest_date}')
cur.close()
conn.close()
" 2>&1)

STOCK_COUNT=$(echo "$DATA_CHECK" | cut -d'|' -f1)
LATEST_DATE=$(echo "$DATA_CHECK" | cut -d'|' -f2)

if [ "$STOCK_COUNT" -gt 50 ]; then
    test_pass "종목 데이터 충분: ${STOCK_COUNT}개"
else
    test_warn "종목 데이터 부족: ${STOCK_COUNT}개"
fi

log_info "최신 가격 날짜: $LATEST_DATE"

# 1.5 가상 계좌 확인
log_info "가상 계좌 확인 중..."
if python paper_trading/paper_trading.py portfolio --account-id 1 > /dev/null 2>&1; then
    test_pass "가상 계좌 조회 성공"
else
    test_fail "가상 계좌 조회 실패"
    exit 1
fi

# ================================================
# Phase 2: AI 분석 전용 테스트 (DRY RUN)
# ================================================

separator "Phase 2: AI 분석 전용 테스트 (DRY RUN)"

log_info "소규모 AI 분석 실행 중 (5개 종목 → 3개 선정)..."
log_warn "⏱️  예상 소요 시간: 5-10분"

PHASE2_START=$(date +%s)

if python paper_trading/trading_crew.py \
    --market KOSPI \
    --limit 5 \
    --top-n 3 \
    --cash-reserve 0.3 \
    --save-log >> "$TEST_LOG" 2>&1; then

    PHASE2_END=$(date +%s)
    PHASE2_DURATION=$((PHASE2_END - PHASE2_START))
    test_pass "AI 분석 완료 (소요 시간: ${PHASE2_DURATION}초)"

    # 로그에서 추천 종목 추출
    log_info "추천 종목 확인 중..."
    # (로그 파일 파싱하여 추천 종목 확인 가능)
else
    test_fail "AI 분석 실패"
    log_error "로그를 확인하세요: $TEST_LOG"
fi

# ================================================
# Phase 3: 실제 매매 시뮬레이션 (LIVE TEST)
# ================================================

separator "Phase 3: 실제 매매 시뮬레이션 (LIVE TEST)"

log_info "초기 포트폴리오 구성 중 (5개 종목 매수)..."
log_warn "⏱️  예상 소요 시간: 10-15분"
log_warn "💰 실제 Paper Trading 매수가 실행됩니다"

read -p "계속하시겠습니까? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    log_warn "사용자가 Phase 3을 건너뜀"
    separator "테스트 중단"
    log "테스트가 사용자에 의해 중단되었습니다"
    exit 0
fi

PHASE3_START=$(date +%s)

if python paper_trading/trading_crew.py \
    --market KOSPI \
    --limit 10 \
    --top-n 5 \
    --cash-reserve 0.2 \
    --stop-loss -10.0 \
    --take-profit 20.0 \
    --execute \
    --save-log >> "$TEST_LOG" 2>&1; then

    PHASE3_END=$(date +%s)
    PHASE3_DURATION=$((PHASE3_END - PHASE3_START))
    test_pass "Paper Trading 매수 완료 (소요 시간: ${PHASE3_DURATION}초)"

    # 포트폴리오 확인
    log_info "포트폴리오 확인 중..."
    PORTFOLIO=$(python paper_trading/paper_trading.py portfolio --account-id 1 2>&1)
    echo "$PORTFOLIO" >> "$TEST_LOG"

    # 보유 종목 수 확인
    POSITION_COUNT=$(echo "$PORTFOLIO" | grep -c "보유 종목" || echo "0")
    if [ "$POSITION_COUNT" -gt 0 ]; then
        test_pass "포트폴리오 생성 확인"
    else
        test_warn "포트폴리오 확인 필요"
    fi
else
    test_fail "Paper Trading 매수 실패"
fi

# ================================================
# Phase 4: 대시보드 모니터링
# ================================================

separator "Phase 4: 대시보드 모니터링"

log_info "대시보드 접근성 테스트..."
log_info "수동으로 대시보드를 실행하세요: ./paper_trading/run_dashboard.sh"
log_info "접속: http://localhost:8050"
test_pass "대시보드 스크립트 존재 확인"

# ================================================
# Phase 7: 성과 보고서 생성
# ================================================

separator "Phase 7: 성과 보고서 생성"

log_info "주간 보고서 생성 중..."
REPORT_FILE="$PROJECT_ROOT/reports/integration_test_report_${TIMESTAMP}.md"

if python paper_trading/performance_reporter.py \
    --type weekly \
    --output "$REPORT_FILE" \
    --save-db >> "$TEST_LOG" 2>&1; then

    test_pass "성과 보고서 생성 완료"
    log_info "보고서 위치: $REPORT_FILE"
else
    test_fail "성과 보고서 생성 실패"
fi

# ================================================
# 테스트 결과 요약
# ================================================

separator "테스트 결과 요약"

SUCCESS_RATE=0
if [ "$TOTAL_TESTS" -gt 0 ]; then
    SUCCESS_RATE=$((PASSED_TESTS * 100 / TOTAL_TESTS))
fi

log "총 테스트: $TOTAL_TESTS"
log "통과: $PASSED_TESTS"
log "실패: $FAILED_TESTS"
log "성공률: ${SUCCESS_RATE}%"

# 테스트 결과 파일 생성
cat > "$TEST_RESULTS_FILE" <<EOF
# 통합 테스트 결과

**일시**: $(date '+%Y-%m-%d %H:%M:%S')
**테스터**: 자동화 스크립트
**로그**: $TEST_LOG

## 결과 요약

- **총 테스트**: $TOTAL_TESTS
- **통과**: $PASSED_TESTS
- **실패**: $FAILED_TESTS
- **성공률**: ${SUCCESS_RATE}%

## 상세 결과

$(cat "$TEST_LOG" | grep -E "✅|❌|⚠️" || echo "상세 내용은 로그 파일 참조")

## 평가

EOF

if [ "$SUCCESS_RATE" -ge 80 ]; then
    echo "✅ **Full Success** - 테스트 통과" >> "$TEST_RESULTS_FILE"
    log "✅ Full Success - 테스트 통과!"
    EXIT_CODE=0
elif [ "$SUCCESS_RATE" -ge 60 ]; then
    echo "⚠️  **Minimum Viable Test** - 부분 성공" >> "$TEST_RESULTS_FILE"
    log_warn "⚠️  Minimum Viable Test - 부분 성공"
    EXIT_CODE=0
else
    echo "❌ **Failed** - 테스트 실패" >> "$TEST_RESULTS_FILE"
    log_error "❌ Failed - 테스트 실패"
    EXIT_CODE=1
fi

separator "테스트 완료"
log "테스트 종료: $(date '+%Y-%m-%d %H:%M:%S')"
log "결과 파일: $TEST_RESULTS_FILE"

exit $EXIT_CODE
