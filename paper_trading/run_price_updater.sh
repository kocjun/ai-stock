#!/bin/bash

# 가격 자동 업데이트 스크립트
# 매일 장 마감 후 주식 가격을 자동으로 업데이트합니다

set -e

# 색상 정의
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 프로젝트 루트 디렉토리
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# PID 파일 경로
PID_FILE="$PROJECT_ROOT/paper_trading/price_updater.pid"
LOG_FILE="$PROJECT_ROOT/paper_trading/logs/price_updater.log"

# stop 명령 처리
if [ "$1" == "stop" ]; then
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            echo -e "${YELLOW}가격 업데이터 종료 중 (PID: $PID)...${NC}"
            kill $PID
            rm -f "$PID_FILE"
            echo -e "${GREEN}✓ 가격 업데이터가 종료되었습니다${NC}"
        else
            echo -e "${YELLOW}가격 업데이터가 실행 중이지 않습니다${NC}"
            rm -f "$PID_FILE"
        fi
    else
        echo -e "${YELLOW}실행 중인 가격 업데이터를 찾을 수 없습니다${NC}"
    fi
    exit 0
fi

# status 명령 처리
if [ "$1" == "status" ]; then
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            echo -e "${GREEN}✓ 가격 업데이터가 실행 중입니다 (PID: $PID)${NC}"
            echo -e "로그 파일: ${YELLOW}$LOG_FILE${NC}"
            echo -e "최신 로그 (tail -f): ${YELLOW}tail -f $LOG_FILE${NC}"
        else
            echo -e "${YELLOW}가격 업데이터가 실행 중이지 않습니다${NC}"
            rm -f "$PID_FILE"
        fi
    else
        echo -e "${YELLOW}실행 중인 가격 업데이터를 찾을 수 없습니다${NC}"
    fi
    exit 0
fi

# logs 디렉터리 생성
mkdir -p "$PROJECT_ROOT/paper_trading/logs"

echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}  가격 자동 업데이트 스크립트${NC}"
echo -e "${GREEN}======================================${NC}"

# 가상환경 활성화
if [ -d ".venv" ]; then
    echo -e "${YELLOW}가상환경 활성화 중...${NC}"
    source .venv/bin/activate
else
    echo -e "${RED}✗ 가상환경을 찾을 수 없습니다: .venv${NC}"
    echo -e "  생성하려면: python3 -m venv .venv"
    exit 1
fi

# 필수 패키지 확인
python -c "import FinanceDataReader" 2>/dev/null || {
    echo -e "${RED}✗ FinanceDataReader 패키지가 없습니다${NC}"
    echo -e "  설치하려면: pip install FinanceDatareader"
    exit 1
}

echo -e "${GREEN}✓ 모든 준비 완료${NC}"
echo ""

# 즉시 실행 또는 백그라운드 실행
if [ "$1" == "--background" ] || [ "$1" == "-b" ]; then
    echo -e "${GREEN}======================================${NC}"
    echo -e "${GREEN}  가격 업데이터 백그라운드 시작${NC}"
    echo -e "${GREEN}======================================${NC}"

    # 백그라운드로 실행
    nohup python paper_trading/price_updater.py > "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"

    echo -e "${GREEN}✓ 가격 업데이터가 백그라운드에서 시작되었습니다${NC}"
    echo -e "PID: ${YELLOW}$(cat $PID_FILE)${NC}"
    echo -e "로그 파일: ${YELLOW}$LOG_FILE${NC}"
    echo -e ""
    echo -e "상태 확인: ${YELLOW}./paper_trading/run_price_updater.sh status${NC}"
    echo -e "종료하려면: ${YELLOW}./paper_trading/run_price_updater.sh stop${NC}"
    echo -e "로그 보기: ${YELLOW}tail -f $LOG_FILE${NC}"
    echo -e "${GREEN}======================================${NC}"
else
    echo -e "${GREEN}======================================${NC}"
    echo -e "${GREEN}  가격 데이터 업데이트 시작${NC}"
    echo -e "${GREEN}======================================${NC}"
    echo ""

    # 즉시 실행
    python paper_trading/price_updater.py
fi
