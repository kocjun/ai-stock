# 디렉토리 재구성 완료 (Option B)

**완료 일시**: 2025-10-30 22:20  
**상태**: ✅ 프로덕션 준비 완료

## 완료된 작업

### 1. 루트 폴더 정리
- ✅ 테스트 파일 3개 → `tests/` 이동
- ✅ 문서 파일 2개 → `docs/` 이동
- ✅ 임시 파일 1개 (investment_status_report.txt) 삭제
- ✅ 루트에는 필수 설정과 가이드만 유지 (8개 파일)

### 2. monitor.sh 심링크 생성
```bash
ln -sf system_monitor/monitor.sh monitor.sh
```

**이점**:
- 루트에서 직접 실행 가능: `./monitor.sh status`
- 일관된 인터페이스 제공

### 3. monitor.sh 개선
#### a. 경로 호환성
```bash
# 루트/system_monitor 양쪽에서 실행 가능하도록 조건 추가
if [ -d "system_monitor" ]; then
    PROJECT_ROOT="$(pwd)"
else
    PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fi
```

#### b. 가상 환경 자동 활성화
```bash
# check_python() 함수에 추가
if [ -f "$PROJECT_ROOT/.venv/bin/activate" ]; then
    source "$PROJECT_ROOT/.venv/bin/activate"
fi
```

### 4. Docker 컨테이너명 표준화
- `investment_db` → `investment_postgres`로 변경
- `processes.json` 업데이트
- `monitor.sh` 도움말 및 명령 업데이트
- 전체 스크립트 일관성 확보

## 최종 루트 디렉토리 구조

```
ai-agent/
├── .env                          (환경 변수)
├── .gitignore                    (Git 설정)
├── requirements.txt              (패키지 목록)
├── monitor.sh → (심링크)         (모니터링)
├── README.md                     (개요)
├── SYSTEM_MONITORING.md          (모니터링 가이드)
├── DAILY_TRADING_SETUP.md        (자동 매매 설정)
└── DIRECTORY_RESTRUCTURE.md      (변경 기록)
```

## 검증 결과

### 상태 조회
```
✅ PRICE_SCHEDULER    - RUNNING
✅ DASHBOARD          - RUNNING
✅ INVESTMENT_POSTGRES - RUNNING
✅ N8N                - RUNNING
✅ 모든 서비스 온라인
```

### 헬스 체크
```
✅ 1개 문제 발견: trading_crew (정상, Cron 스케줄)
✅ 모든 시스템 정상
```

### 기능 점검
- ✅ `./monitor.sh status` - 정상
- ✅ `./monitor.sh health` - 정상
- ✅ `./monitor.sh help` - 정상
- ✅ 경로 호환성 - 완벽
- ✅ 설정 파일 파싱 - 정상

## 사용 방법

### 루트에서 실행
```bash
./monitor.sh status              # 상태 확인
./monitor.sh health              # 헬스 체크
./monitor.sh help                # 도움말
```

### 직접 Python 실행
```bash
source .venv/bin/activate
python3 system_monitor/system_monitor.py status
python3 system_monitor/system_monitor.py health
```

## 이점

1. **가독성**: 루트는 8개 파일만 유지 (매우 깔끔)
2. **유지보수성**: 테스트/문서가 한곳에 정리됨
3. **사용성**: monitor.sh를 루트에서 직접 실행 가능
4. **안정성**: 경로 문제로 인한 오류 최소화
5. **일관성**: Docker 컨테이너명 통일

## Git 커밋 예시
```bash
git add .
git commit -m "refactor: Reorganize directory structure

- Move test files to tests/ directory
- Move documentation to docs/ directory
- Delete temporary report files
- Create monitor.sh symlink in root
- Update container name: investment_db → investment_postgres
- Improve path compatibility and venv activation in monitor.sh"
```

