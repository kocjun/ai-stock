#!/bin/bash

# ================================================
# 일일 페이퍼 트레이딩 실행 스크립트
# ================================================

# 프로젝트 루트 디렉토리
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

# Python 가상환경 활성화
source .venv/bin/activate

# 로그 디렉토리 생성
LOG_DIR="$PROJECT_ROOT/paper_trading/logs"
mkdir -p "$LOG_DIR"

# 로그 파일
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="$LOG_DIR/trading_${TIMESTAMP}.log"

echo "============================================================" | tee -a "$LOG_FILE"
echo "일일 페이퍼 트레이딩 실행" | tee -a "$LOG_FILE"
echo "시작 시간: $(date '+%Y-%m-%d %H:%M:%S')" | tee -a "$LOG_FILE"
echo "============================================================" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# 설정
ACCOUNT_ID=1
MARKET="KOSPI"
LIMIT=20
TOP_N=10
CASH_RESERVE=0.2
STOP_LOSS=-10.0
TAKE_PROFIT=20.0

# 실제 매매 실행 여부 (--execute 플래그 추가 시 실제 매매)
# 테스트 기간에는 --execute 제거하여 분석만 수행
EXECUTE_FLAG="--execute"  # 실제 매매 실행 (DRY RUN으로 하려면: EXECUTE_FLAG="")

# 페이퍼 트레이딩 실행
python3 "$PROJECT_ROOT/paper_trading/trading_crew.py" \
    --account-id "$ACCOUNT_ID" \
    --market "$MARKET" \
    --limit "$LIMIT" \
    --top-n "$TOP_N" \
    --cash-reserve "$CASH_RESERVE" \
    --stop-loss "$STOP_LOSS" \
    --take-profit "$TAKE_PROFIT" \
    $EXECUTE_FLAG \
    --save-log \
    2>&1 | tee -a "$LOG_FILE"

EXIT_CODE=$?

echo "" | tee -a "$LOG_FILE"
echo "============================================================" | tee -a "$LOG_FILE"
if [ $EXIT_CODE -eq 0 ]; then
    echo "✓ 일일 트레이딩 완료" | tee -a "$LOG_FILE"

    # 이메일 전송 (성공 시에만)
    echo "" | tee -a "$LOG_FILE"
    echo "[이메일 전송]" | tee -a "$LOG_FILE"

    # 가장 최근 결과 파일 찾기
    LATEST_RESULT=$(ls -t "$LOG_DIR"/trading_workflow_*.json 2>/dev/null | head -1)

    if [ -n "$LATEST_RESULT" ]; then
        echo "결과 파일: $LATEST_RESULT" | tee -a "$LOG_FILE"
        python3 -c "
from core.utils.email_sender import send_trading_result_email
import sys
success = send_trading_result_email('$LATEST_RESULT')
sys.exit(0 if success else 1)
" 2>&1 | tee -a "$LOG_FILE"

        if [ $? -eq 0 ]; then
            echo "✓ 이메일 전송 완료" | tee -a "$LOG_FILE"
        else
            echo "✗ 이메일 전송 실패 (.env 파일의 이메일 설정을 확인하세요)" | tee -a "$LOG_FILE"
        fi
    else
        echo "✗ 결과 파일을 찾을 수 없습니다" | tee -a "$LOG_FILE"
    fi
else
    echo "✗ 일일 트레이딩 실패 (exit code: $EXIT_CODE)" | tee -a "$LOG_FILE"
fi
echo "종료 시간: $(date '+%Y-%m-%d %H:%M:%S')" | tee -a "$LOG_FILE"
echo "============================================================" | tee -a "$LOG_FILE"

# 가상환경 비활성화
deactivate

exit $EXIT_CODE
