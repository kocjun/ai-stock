#!/bin/bash

# 가격 업데이트 스케줄러 실행 스크립트
# 백그라운드에서 정기적으로 가격을 업데이트합니다

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
PID_FILE="$PROJECT_ROOT/paper_trading/price_scheduler.pid"
LOG_FILE="$PROJECT_ROOT/paper_trading/logs/price_scheduler.log"

# 스케줄 타입 (기본: daily)
SCHEDULE_TYPE="${1:-daily}"

# stop 명령 처리
if [ "$1" == "stop" ]; then
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            echo -e "${YELLOW}가격 스케줄러 종료 중 (PID: $PID)...${NC}"
            kill $PID
            sleep 2
            rm -f "$PID_FILE"
            echo -e "${GREEN}✓ 가격 스케줄러가 종료되었습니다${NC}"
        else
            echo -e "${YELLOW}가격 스케줄러가 실행 중이지 않습니다${NC}"
            rm -f "$PID_FILE"
        fi
    else
        echo -e "${YELLOW}실행 중인 가격 스케줄러를 찾을 수 없습니다${NC}"
    fi
    exit 0
fi

# status 명령 처리
if [ "$1" == "status" ]; then
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            echo -e "${GREEN}✓ 가격 스케줄러가 실행 중입니다 (PID: $PID)${NC}"
            echo -e "로그 파일: ${YELLOW}$LOG_FILE${NC}"
            echo -e "최신 로그 (tail -f): ${YELLOW}tail -f $LOG_FILE${NC}"
        else
            echo -e "${YELLOW}가격 스케줄러가 실행 중이지 않습니다${NC}"
            rm -f "$PID_FILE"
        fi
    else
        echo -e "${YELLOW}실행 중인 가격 스케줄러를 찾을 수 없습니다${NC}"
    fi
    exit 0
fi

# logs 디렉터리 생성
mkdir -p "$PROJECT_ROOT/paper_trading/logs"

echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}  가격 업데이트 스케줄러${NC}"
echo -e "${GREEN}======================================${NC}"

# 이미 실행 중인지 확인
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p $PID > /dev/null 2>&1; then
        echo -e "${YELLOW}가격 스케줄러가 이미 실행 중입니다 (PID: $PID)${NC}"
        echo -e "상태 확인: ${YELLOW}./paper_trading/run_price_scheduler.sh status${NC}"
        echo -e "종료하려면: ${YELLOW}./paper_trading/run_price_scheduler.sh stop${NC}"
        exit 1
    else
        rm -f "$PID_FILE"
    fi
fi

# 가상환경 활성화
if [ -d ".venv" ]; then
    echo -e "${YELLOW}가상환경 활성화 중...${NC}"
    source .venv/bin/activate
else
    echo -e "${RED}✗ 가상환경을 찾을 수 없습니다: .venv${NC}"
    echo -e "  생성하려면: python3 -m venv .venv"
    exit 1
fi

# APScheduler 패키지 확인
python -c "import apscheduler" 2>/dev/null || {
    echo -e "${RED}✗ APScheduler 패키지가 없습니다${NC}"
    echo -e "  설치하려면: pip install apscheduler"
    exit 1
}

echo -e "${GREEN}✓ 모든 준비 완료${NC}"
echo ""

# 스케줄 타입 확인
case "$SCHEDULE_TYPE" in
    daily)
        echo -e "${YELLOW}스케줄 타입: 일일 (평일 15:40)${NC}"
        ;;
    hourly)
        echo -e "${YELLOW}스케줄 타입: 시간별 (매 시간 정각) - 테스트용${NC}"
        ;;
    market)
        echo -e "${YELLOW}스케줄 타입: 장 운영 시간 (09:00~16:00, 30분 간격) - 개발용${NC}"
        ;;
    *)
        echo -e "${RED}✗ 알 수 없는 스케줄 타입: $SCHEDULE_TYPE${NC}"
        echo -e "  사용 가능: daily, hourly, market"
        exit 1
        ;;
esac

echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}  가격 스케줄러 백그라운드 시작${NC}"
echo -e "${GREEN}======================================${NC}"

# 백그라운드로 실행
nohup python paper_trading/price_scheduler.py --schedule "$SCHEDULE_TYPE" > "$LOG_FILE" 2>&1 &
echo $! > "$PID_FILE"

sleep 1

# 프로세스가 정상 시작되었는지 확인
if ps -p $(cat "$PID_FILE") > /dev/null 2>&1; then
    echo -e "${GREEN}✓ 가격 스케줄러가 백그라운드에서 시작되었습니다${NC}"
    echo -e "PID: ${YELLOW}$(cat $PID_FILE)${NC}"
    echo -e "로그 파일: ${YELLOW}$LOG_FILE${NC}"
    echo -e ""
    echo -e "상태 확인: ${YELLOW}./paper_trading/run_price_scheduler.sh status${NC}"
    echo -e "종료하려면: ${YELLOW}./paper_trading/run_price_scheduler.sh stop${NC}"
    echo -e "로그 보기: ${YELLOW}tail -f $LOG_FILE${NC}"
    echo -e "${GREEN}======================================${NC}"
else
    echo -e "${RED}✗ 가격 스케줄러 시작 실패${NC}"
    echo -e "로그를 확인하세요: ${YELLOW}tail -20 $LOG_FILE${NC}"
    rm -f "$PID_FILE"
    exit 1
fi
