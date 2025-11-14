#!/bin/bash

###############################################################################
# 주간 투자 분석 자동화 스크립트
#
# 실행 내용:
# 1. Docker 서비스 상태 체크 (PostgreSQL, n8n)
# 2. Ollama 서비스 상태 체크
# 3. 통합 워크플로 실행 (integrated_crew.py)
# 4. 주간 리포트 생성 및 저장
# 5. n8n Webhook 알림 전송
#
# Cron 설정 예시:
# 0 9 * * 6 /path/to/run_weekly_analysis.sh
# (매주 토요일 오전 9시 실행)
###############################################################################

set -e  # 오류 발생 시 중단

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 로그 디렉터리 생성
LOG_DIR="./logs"
mkdir -p $LOG_DIR

# 리포트 디렉터리 생성
REPORT_DIR="./reports"
mkdir -p $REPORT_DIR

# 타임스탬프
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="$LOG_DIR/weekly_analysis_$TIMESTAMP.log"

# 로그 함수
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a $LOG_FILE
}

log_success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] ✓${NC} $1" | tee -a $LOG_FILE
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ✗${NC} $1" | tee -a $LOG_FILE
}

log_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] ⚠${NC} $1" | tee -a $LOG_FILE
}

###############################################################################
# 1. Docker 서비스 체크
###############################################################################

log "===== 주간 투자 분석 시작 ====="
log "타임스탬프: $TIMESTAMP"
log ""

log "단계 1: Docker 서비스 상태 확인"

# PostgreSQL 체크
if docker ps | grep -q investment_postgres; then
    log_success "PostgreSQL 컨테이너 실행 중"
else
    log_error "PostgreSQL 컨테이너가 실행되지 않음"
    log "PostgreSQL 시작 중..."
    docker-compose up -d postgres
    sleep 5

    if docker ps | grep -q investment_postgres; then
        log_success "PostgreSQL 시작 완료"
    else
        log_error "PostgreSQL 시작 실패. 스크립트 종료."
        exit 1
    fi
fi

# n8n 체크
if docker ps | grep -q n8n; then
    log_success "n8n 컨테이너 실행 중"
else
    log_warning "n8n 컨테이너가 실행되지 않음 (선택적)"
fi

log ""

###############################################################################
# 2. Ollama 서비스 체크
###############################################################################

log "단계 2: Ollama 서비스 상태 확인"

if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    log_success "Ollama 서버 실행 중"

    # 모델 확인
    if curl -s http://localhost:11434/api/tags | grep -q "llama3.1"; then
        log_success "llama3.1 모델 사용 가능"
    else
        log_warning "llama3.1 모델이 없습니다. 다른 모델 사용 가능"
    fi
else
    log_error "Ollama 서버가 실행되지 않음"
    log "Ollama를 시작하세요: ollama serve"
    exit 1
fi

log ""

###############################################################################
# 3. Python 가상환경 활성화
###############################################################################

log "단계 3: Python 가상환경 활성화"

if [ -d ".venv" ]; then
    source .venv/bin/activate
    log_success "가상환경 활성화 완료"
else
    log_error "가상환경이 없습니다 (.venv)"
    log "가상환경을 생성하세요: python3 -m venv .venv"
    exit 1
fi

log ""

###############################################################################
# 4. 통합 워크플로 실행
###############################################################################

log "단계 4: 통합 투자 분석 워크플로 실행"
log "실행 파일: integrated_crew.py"

# Python 스크립트 실행
if python integrated_crew.py >> $LOG_FILE 2>&1; then
    log_success "통합 워크플로 실행 완료"
else
    log_error "통합 워크플로 실행 실패"
    log "로그 파일을 확인하세요: $LOG_FILE"
    exit 1
fi

log ""

###############################################################################
# 5. 주간 리포트 생성 (백테스팅 포함)
###############################################################################

log "단계 5: 주간 백테스트 리포트 생성"

# 최근 3개월 백테스트 실행
if python -c "
from backtesting import run_backtest, generate_backtest_report
from datetime import datetime, timedelta

end_date = datetime.now().strftime('%Y-%m-%d')
start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')

result = run_backtest(
    start_date=start_date,
    end_date=end_date,
    strategy='equal_weight',
    top_n=10
)

if result['status'] == 'success':
    report_file = 'reports/weekly_backtest_${TIMESTAMP}.md'
    generate_backtest_report(result, report_file)
    print(f'리포트 저장: {report_file}')
" >> $LOG_FILE 2>&1; then
    log_success "백테스트 리포트 생성 완료"
else
    log_warning "백테스트 리포트 생성 실패 (선택적)"
fi

log ""

###############################################################################
# 6. 알림 전송 (n8n Webhook)
###############################################################################

log "단계 6: 알림 전송 (n8n Webhook)"

# .env에서 웹훅 URL 로드
if [ -f ".env" ]; then
    source .env

    if [ ! -z "$N8N_WEBHOOK_URL" ]; then
        # Webhook 전송
        curl -X POST $N8N_WEBHOOK_URL \
            -H "Content-Type: application/json" \
            -d "{
                \"type\": \"weekly_analysis\",
                \"status\": \"success\",
                \"timestamp\": \"$TIMESTAMP\",
                \"message\": \"주간 투자 분석 완료\",
                \"log_file\": \"$LOG_FILE\"
            }" > /dev/null 2>&1

        if [ $? -eq 0 ]; then
            log_success "n8n Webhook 알림 전송 완료"
        else
            log_warning "n8n Webhook 알림 전송 실패 (선택적)"
        fi
    else
        log_warning "N8N_WEBHOOK_URL이 설정되지 않음 (선택적)"
    fi
else
    log_warning ".env 파일이 없음 (선택적)"
fi

log ""

###############################################################################
# 7. 완료
###############################################################################

log_success "===== 주간 투자 분석 완료 ====="
log "로그 파일: $LOG_FILE"
log "리포트 디렉터리: $REPORT_DIR"
log ""

# 최근 리포트 파일 목록
log "최근 생성된 리포트:"
ls -lt $REPORT_DIR | head -5 | tee -a $LOG_FILE

log ""
log "다음 실행: 다음 주 토요일 오전 9시"
log "Cron 설정 확인: crontab -l"

exit 0
