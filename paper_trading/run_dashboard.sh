#!/bin/bash

# Paper Trading Dashboard 실행 스크립트

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
PID_FILE="$PROJECT_ROOT/paper_trading/dashboard.pid"
LOG_FILE="$PROJECT_ROOT/paper_trading/dashboard.log"

# 백그라운드 모드 확인
BACKGROUND_MODE=false
if [ "$1" == "--background" ] || [ "$1" == "-b" ]; then
    BACKGROUND_MODE=true
fi

# stop 명령 처리
if [ "$1" == "stop" ]; then
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            echo -e "${YELLOW}대시보드 종료 중 (PID: $PID)...${NC}"
            kill $PID
            rm -f "$PID_FILE"
            echo -e "${GREEN}✓ 대시보드가 종료되었습니다${NC}"
        else
            echo -e "${YELLOW}대시보드가 실행 중이지 않습니다${NC}"
            rm -f "$PID_FILE"
        fi
    else
        echo -e "${YELLOW}실행 중인 대시보드를 찾을 수 없습니다${NC}"
    fi
    exit 0
fi

# status 명령 처리
if [ "$1" == "status" ]; then
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            echo -e "${GREEN}✓ 대시보드가 실행 중입니다 (PID: $PID)${NC}"
            echo -e "접속 주소: ${YELLOW}http://localhost:8050${NC}"
            echo -e "로그 파일: ${YELLOW}$LOG_FILE${NC}"
        else
            echo -e "${YELLOW}대시보드가 실행 중이지 않습니다${NC}"
            rm -f "$PID_FILE"
        fi
    else
        echo -e "${YELLOW}실행 중인 대시보드를 찾을 수 없습니다${NC}"
    fi
    exit 0
fi

# 이미 실행 중인지 확인
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p $PID > /dev/null 2>&1; then
        echo -e "${YELLOW}대시보드가 이미 실행 중입니다 (PID: $PID)${NC}"
        echo -e "접속 주소: ${YELLOW}http://localhost:8050${NC}"
        echo -e "종료하려면: ${YELLOW}./paper_trading/run_dashboard.sh stop${NC}"
        exit 1
    else
        rm -f "$PID_FILE"
    fi
fi

echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}  Paper Trading Dashboard${NC}"
echo -e "${GREEN}======================================${NC}"

# 가상환경 활성화
if [ -d ".venv" ]; then
    echo -e "${YELLOW}가상환경 활성화 중...${NC}"
    source .venv/bin/activate
else
    echo -e "${RED}가상환경을 찾을 수 없습니다: .venv${NC}"
    echo -e "${YELLOW}다음 명령으로 가상환경을 생성하세요:${NC}"
    echo -e "  python3 -m venv .venv"
    echo -e "  source .venv/bin/activate"
    echo -e "  pip install -r requirements.txt"
    exit 1
fi

# 의존성 확인
echo -e "${YELLOW}의존성 확인 중...${NC}"
if ! python -c "import dash" 2>/dev/null; then
    echo -e "${YELLOW}Dash가 설치되어 있지 않습니다. 설치 중...${NC}"
    pip install -q dash dash-bootstrap-components
fi

# PostgreSQL 연결 확인
echo -e "${YELLOW}데이터베이스 연결 확인 중...${NC}"
if ! python -c "from core.utils.db_utils import get_db_connection; conn = get_db_connection(); conn.close()" 2>/dev/null; then
    echo -e "${RED}데이터베이스 연결 실패${NC}"
    echo -e "${YELLOW}다음을 확인하세요:${NC}"
    echo -e "  1. Docker PostgreSQL 컨테이너가 실행 중인지 확인"
    echo -e "     docker ps | grep investment_postgres"
    echo -e "  2. .env 파일의 DB 설정 확인"
    exit 1
fi

echo -e "${GREEN}✓ 모든 준비 완료${NC}"
echo ""

# 대시보드 실행
cd paper_trading

if [ "$BACKGROUND_MODE" = true ]; then
    echo -e "${GREEN}======================================${NC}"
    echo -e "${GREEN}  대시보드 백그라운드 시작${NC}"
    echo -e "${GREEN}======================================${NC}"

    # 백그라운드로 실행
    nohup python dashboard.py > "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"

    echo -e "${GREEN}✓ 대시보드가 백그라운드에서 시작되었습니다${NC}"
    echo -e "PID: ${YELLOW}$(cat $PID_FILE)${NC}"
    echo -e "접속 주소: ${YELLOW}http://localhost:8050${NC}"
    echo -e "로그 파일: ${YELLOW}$LOG_FILE${NC}"
    echo -e ""
    echo -e "상태 확인: ${YELLOW}./paper_trading/run_dashboard.sh status${NC}"
    echo -e "종료하려면: ${YELLOW}./paper_trading/run_dashboard.sh stop${NC}"
    echo -e "로그 보기: ${YELLOW}tail -f $LOG_FILE${NC}"
    echo -e "${GREEN}======================================${NC}"
else
    echo -e "${GREEN}======================================${NC}"
    echo -e "${GREEN}  대시보드 시작${NC}"
    echo -e "${GREEN}======================================${NC}"
    echo -e "접속 주소: ${YELLOW}http://localhost:8050${NC}"
    echo -e "종료하려면: ${YELLOW}Ctrl+C${NC}"
    echo -e "${GREEN}======================================${NC}"
    echo ""

    # 포그라운드로 실행
    python dashboard.py
fi
