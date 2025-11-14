#!/bin/bash

###############################################################################
# 일일 자동 매매 실행 스크립트
#
# 역할: 매일 오전 9시 정각에 종목별 주도주 전략 기반 매매 실행
# 사용: Cron 스케줄러에 등록하여 자동 실행
# 로그: paper_trading/trading_daily.log에 기록
###############################################################################

# 프로젝트 루트 디렉토리
PROJECT_ROOT="/Users/yeongchang.jeon/workspace/ai-agent"

# 로그 파일
LOG_FILE="$PROJECT_ROOT/paper_trading/trading_daily.log"

# 가상 환경 활성화
source "$PROJECT_ROOT/.venv/bin/activate"

# 작업 디렉토리로 이동
cd "$PROJECT_ROOT"

# 타임스탬프 추가
echo "========================================" >> "$LOG_FILE"
echo "시작 시간: $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"

# 주도주 전략으로 일일 자동 매매 실행
python3 paper_trading/trading_crew.py \
    --strategy leader \
    --top-n 10 \
    --execute \
    >> "$LOG_FILE" 2>&1

# 실행 결과 기록
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ 매매 완료 (종료 코드: $EXIT_CODE)" >> "$LOG_FILE"
else
    echo "⚠️  매매 중 오류 발생 (종료 코드: $EXIT_CODE)" >> "$LOG_FILE"
fi

echo "종료 시간: $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

exit $EXIT_CODE
