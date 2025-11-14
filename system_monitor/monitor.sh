#!/bin/bash

################################################################################
# 시스템 프로세스 모니터링 및 관리 스크립트
#
# 사용법:
#   ./monitor.sh status                    # 전체 상태 확인
#   ./monitor.sh start <process_name>      # 프로세스 시작
#   ./monitor.sh restart <process_name>    # 프로세스 재시작
#   ./monitor.sh health                    # 시스템 상태 점검
#   ./monitor.sh setup                     # 초기 설정
################################################################################

set -e

# 프로젝트 루트 경로
# 이 스크립트가 루트 또는 system_monitor에서 실행될 수 있도록 처리
if [ -d "system_monitor" ]; then
    PROJECT_ROOT="$(pwd)"
else
    PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fi
MONITOR_DIR="$PROJECT_ROOT/system_monitor"
PYTHON_CMD="python3"

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 함수: 메시지 출력
print_status() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# 함수: Python 실행 경로 확인 및 가상 환경 활성화
check_python() {
    # 가상 환경 활성화
    if [ -f "$PROJECT_ROOT/.venv/bin/activate" ]; then
        source "$PROJECT_ROOT/.venv/bin/activate"
    fi

    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
        print_success "Python3 found: $(python3 --version)"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
        print_success "Python found: $(python --version)"
    else
        print_error "Python not found!"
        exit 1
    fi
}

# 함수: 모니터링 시작
start_monitoring() {
    print_status "시스템 모니터링 시작 중..."
    cd "$PROJECT_ROOT"

    # Python 프로세스 시작
    print_status "가격 업데이트 스케줄러 시작..."
    $PYTHON_CMD system_monitor/system_monitor.py start price_scheduler

    print_status "대시보드 시작..."
    $PYTHON_CMD system_monitor/system_monitor.py start dashboard

    # Docker 컨테이너 시작
    print_status "PostgreSQL 데이터베이스 시작..."
    docker start investment_postgres 2>/dev/null || print_warning "investment_postgres 컨테이너를 찾을 수 없습니다"

    print_status "N8N 자동화 플랫폼 시작..."
    docker start n8n 2>/dev/null || print_warning "n8n 컨테이너를 찾을 수 없습니다"

    print_success "모니터링 시작 완료"
    print_status "대시보드: http://localhost:8050"
    print_status "N8N: http://localhost:5678"
}

# 함수: 모니터링 중지
stop_monitoring() {
    print_status "시스템 모니터링 중지 중..."

    # Python 프로세스 종료
    print_status "가격 업데이트 스케줄러 종료..."
    $PYTHON_CMD system_monitor/system_monitor.py stop price_scheduler 2>/dev/null || true

    print_status "대시보드 종료..."
    $PYTHON_CMD system_monitor/system_monitor.py stop dashboard 2>/dev/null || true

    # Docker 컨테이너 종료
    print_status "PostgreSQL 데이터베이스 중지..."
    docker stop investment_postgres 2>/dev/null || print_warning "investment_postgres 컨테이너를 찾을 수 없습니다"

    print_status "N8N 자동화 플랫폼 중지..."
    docker stop n8n 2>/dev/null || print_warning "n8n 컨테이너를 찾을 수 없습니다"

    print_success "모니터링 중지 완료"
}

# 함수: 도움말 출력
show_help() {
    cat << EOF
${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🖥️  시스템 프로세스 모니터링 및 관리 도구
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}

${GREEN}명령어:${NC}
  status              상태 대시보드 표시
  start               모든 프로세스/컨테이너 시작
  stop                모든 프로세스/컨테이너 중지
  restart             모든 프로세스/컨테이너 재시작
  health              시스템 상태 점검
  setup               초기 설정

${GREEN}개별 프로세스 관리:${NC}
  $PYTHON_CMD system_monitor/system_monitor.py status
  $PYTHON_CMD system_monitor/system_monitor.py start price_scheduler
  $PYTHON_CMD system_monitor/system_monitor.py restart dashboard
  $PYTHON_CMD system_monitor/system_monitor.py docker-start investment_postgres

${GREEN}예시:${NC}
  ./monitor.sh status                    # 전체 상태 확인
  ./monitor.sh start                     # 모든 프로세스 시작
  ./monitor.sh health                    # 시스템 점검
  ./monitor.sh stop                      # 모든 프로세스 중지

${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}
EOF
}

# 메인 스크립트
main() {
    check_python

    case "${1:-status}" in
        status)
            $PYTHON_CMD "$MONITOR_DIR/system_monitor.py" status
            ;;
        start)
            start_monitoring
            ;;
        stop)
            stop_monitoring
            ;;
        restart)
            stop_monitoring
            sleep 2
            start_monitoring
            ;;
        health)
            $PYTHON_CMD "$MONITOR_DIR/system_monitor.py" health
            ;;
        setup)
            print_status "초기 설정 중..."
            mkdir -p "$MONITOR_DIR"
            chmod +x "$0"
            print_success "초기 설정 완료"
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "알 수 없는 명령어: $1"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

main "$@"
