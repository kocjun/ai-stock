#!/bin/bash

# 컨테이너 내부에서 통합 테스트 실행
# 사용법:
#   ./scripts/run_tests_in_container.sh            # 기본 통합 테스트
#   ./scripts/run_tests_in_container.sh "pytest"  # 임의 명령 실행

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
DOCKER_DIR="${PROJECT_ROOT}/docker"

COMMAND=${1:-"./tests/run_integration_test.sh"}

if [ ! -d "${DOCKER_DIR}" ]; then
    echo "docker 디렉터리를 찾을 수 없습니다. 경로를 확인하세요." >&2
    exit 1
fi

cd "${DOCKER_DIR}"
docker compose --env-file ../.env exec ai-stock-app bash -lc "${COMMAND}"
