#!/bin/bash

# ================================================
# 주간 성과 보고서 생성 스크립트
# ================================================

# 프로젝트 루트 디렉토리
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

# Python 가상환경 활성화
source .venv/bin/activate

# 로그 디렉토리 생성
LOG_DIR="$PROJECT_ROOT/paper_trading/logs"
REPORT_DIR="$PROJECT_ROOT/paper_trading/reports"
mkdir -p "$LOG_DIR"
mkdir -p "$REPORT_DIR"

# 로그 파일
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="$LOG_DIR/report_${TIMESTAMP}.log"

echo "============================================================" | tee -a "$LOG_FILE"
echo "주간 성과 보고서 생성" | tee -a "$LOG_FILE"
echo "시작 시간: $(date '+%Y-%m-%d %H:%M:%S')" | tee -a "$LOG_FILE"
echo "============================================================" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# 설정
ACCOUNT_ID=1
REPORT_TYPE="weekly"
REPORT_FILE="$REPORT_DIR/weekly_report_$(date +%Y%m%d).md"

# 보고서 생성 (HTML 형식으로 N8N 전송, 마크다운은 로컬 저장)
python3 "$PROJECT_ROOT/paper_trading/performance_reporter.py" \
    --account-id "$ACCOUNT_ID" \
    --type "$REPORT_TYPE" \
    --output "$REPORT_FILE" \
    --save-db \
    --send-n8n \
    2>&1 | tee -a "$LOG_FILE"

EXIT_CODE=$?

echo "" | tee -a "$LOG_FILE"
echo "============================================================" | tee -a "$LOG_FILE"
if [ $EXIT_CODE -eq 0 ]; then
    echo "✓ 주간 보고서 생성 완료" | tee -a "$LOG_FILE"
    echo "  파일: $REPORT_FILE" | tee -a "$LOG_FILE"
else
    echo "✗ 주간 보고서 생성 실패 (exit code: $EXIT_CODE)" | tee -a "$LOG_FILE"
fi
echo "종료 시간: $(date '+%Y-%m-%d %H:%M:%S')" | tee -a "$LOG_FILE"
echo "============================================================" | tee -a "$LOG_FILE"

# 가상환경 비활성화
deactivate

exit $EXIT_CODE
