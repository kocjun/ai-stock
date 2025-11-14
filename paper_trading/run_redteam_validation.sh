#!/bin/bash

# ================================================
# 레드팀 검증 실행 스크립트
# ================================================

# 프로젝트 루트 디렉토리
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

# Python 가상환경 활성화 (있는 경우)
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi

# 로그 디렉토리 생성
LOG_DIR="$PROJECT_ROOT/paper_trading/logs/redteam"
mkdir -p "$LOG_DIR"

# 로그 파일
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="$LOG_DIR/validation_${TIMESTAMP}.log"

echo "============================================================" | tee -a "$LOG_FILE"
echo "🔴 레드팀 검증 실행" | tee -a "$LOG_FILE"
echo "시작 시간: $(date '+%Y-%m-%d %H:%M:%S')" | tee -a "$LOG_FILE"
echo "============================================================" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# 설정
ACCOUNT_ID=1
MARKET="KOSPI"
LIMIT=20
TOP_N=10

echo "설정:" | tee -a "$LOG_FILE"
echo "  계좌 ID: $ACCOUNT_ID" | tee -a "$LOG_FILE"
echo "  시장: $MARKET" | tee -a "$LOG_FILE"
echo "  분석 종목 수: $LIMIT" | tee -a "$LOG_FILE"
echo "  선정 종목 수: $TOP_N" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# 레드팀 검증 실행
python3 "$PROJECT_ROOT/paper_trading/redteam_validator.py" \
    --account-id "$ACCOUNT_ID" \
    --market "$MARKET" \
    --limit "$LIMIT" \
    --top-n "$TOP_N" \
    2>&1 | tee -a "$LOG_FILE"

EXIT_CODE=$?

echo "" | tee -a "$LOG_FILE"
echo "============================================================" | tee -a "$LOG_FILE"
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ 레드팀 검증 완료" | tee -a "$LOG_FILE"

    # 이메일 전송 (성공 시에만)
    echo "" | tee -a "$LOG_FILE"
    echo "[이메일 전송]" | tee -a "$LOG_FILE"

    # 가장 최근 검증 결과 파일 찾기
    LATEST_RESULT=$(ls -t "$LOG_DIR"/redteam_validation_*.json 2>/dev/null | head -1)

    if [ -n "$LATEST_RESULT" ]; then
        echo "결과 파일: $LATEST_RESULT" | tee -a "$LOG_FILE"
        python3 -c "
from core.utils.email_sender import send_redteam_result_email
import sys
success = send_redteam_result_email('$LATEST_RESULT')
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
    echo "❌ 레드팀 검증 실패 (exit code: $EXIT_CODE)" | tee -a "$LOG_FILE"
fi
echo "종료 시간: $(date '+%Y-%m-%d %H:%M:%S')" | tee -a "$LOG_FILE"
echo "============================================================" | tee -a "$LOG_FILE"

# 가상환경 비활성화
if [ -f ".venv/bin/activate" ]; then
    deactivate
fi

exit $EXIT_CODE
