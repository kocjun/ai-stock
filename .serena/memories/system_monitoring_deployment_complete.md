# 시스템 모니터링 도구 배포 완료

## 완료된 작업

### 1. 핵심 모니터링 엔진
**파일: `system_monitor/system_monitor.py` (520 줄)**

주요 기능:
- Python 프로세스 모니터링 (price_scheduler, dashboard, trading_crew)
- Docker 컨테이너 관리 (PostgreSQL investment_db, N8N)
- 서비스 포트 가용성 점검 (5432, 11434, 5678, 8050)
- 실시간 CPU/메모리 모니터링
- PID 파일 기반 프로세스 제어
- 타임스탬프가 있는 로깅 시스템

### 2. 사용자 인터페이스
**파일: `system_monitor/monitor.sh`**

CLI 명령어:
- `./monitor.sh status` - 전체 상태 대시보드
- `./monitor.sh start` - 모든 프로세스 시작
- `./monitor.sh stop` - 모든 프로세스 중지
- `./monitor.sh restart` - 모든 프로세스 재시작
- `./monitor.sh health` - 시스템 헬스 체크
- `./monitor.sh help` - 도움말 표시

색상 코드 UI:
- 🟢 RUNNING (초록색)
- 🔴 STOPPED (빨간색)
- 🟠 ERROR (주황색)
- 🟡 UNKNOWN (노란색)
- ✅ ONLINE (온라인)
- ❌ OFFLINE (오프라인)

### 3. 설정 파일
**파일: `system_monitor/processes.json`**

관리 대상:
1. Python 프로세스:
   - price_scheduler (자동 가격 업데이트)
   - dashboard (포트 8050)
   - trading_crew (AI 매매 워크플로우)

2. Docker 컨테이너:
   - investment_db (PostgreSQL, 포트 5432)
   - n8n (자동화 플랫폼, 포트 5678)

3. 외부 서비스:
   - PostgreSQL (5432)
   - Ollama (11434)
   - N8N (5678)
   - Dashboard (8050)

### 4. 문서화
**파일들:**
- `system_monitor/README.md` - 400줄 기술 문서
- `system_monitor/QUICKSTART.md` - 빠른 시작 가이드
- `SYSTEM_MONITORING.md` (루트) - 500줄 종합 가이드

내용:
- 설치 및 설정 방법
- 모든 명령어 상세 설명
- 트러블슈팅 가이드
- Cron/LaunchAgent 자동화 방법
- 로그 확인 방법

## 현재 시스템 상태 (2025-10-30)

```
🖥️  시스템 프로세스 모니터링 대시보드

📌 Python 백그라운드 프로세스
🔴 PRICE_SCHEDULER    - STOPPED
🔴 TRADING_CREW       - STOPPED
🔴 DASHBOARD          - STOPPED

📦 Docker 컨테이너
❓ INVESTMENT_DB      - NOT_FOUND
🟢 N8N                - RUNNING

🌐 서비스 가용성
✅ PostgreSQL (5432)   - 온라인
✅ Ollama (11434)      - 온라인
✅ N8N (5678)          - 온라인
❌ Dashboard (8050)    - 오프라인
```

## 주요 기능

### 프로세스 제어
```bash
# 가격 업데이터 시작
python3 system_monitor.py start price_scheduler

# 대시보드 시작
python3 system_monitor.py start dashboard

# 특정 프로세스 중지
python3 system_monitor.py stop price_scheduler

# 프로세스 재시작
python3 system_monitor.py restart dashboard
```

### Docker 관리
```bash
# PostgreSQL 시작
python3 system_monitor.py docker-start investment_db

# N8N 중지
python3 system_monitor.py docker-stop n8n
```

### 자동화 설정
Cron 작업 예시:
```bash
# 매 30분마다 헬스 체크
*/30 * * * * cd /Users/yeongchang.jeon/workspace/ai-agent && source .venv/bin/activate && python3 system_monitor/system_monitor.py health >> system_monitor/monitor.log 2>&1

# 매일 오전 9시 상태 확인
0 9 * * * cd /Users/yeongchang.jeon/workspace/ai-agent && source .venv/bin/activate && ./system_monitor/monitor.sh status >> system_monitor/monitor.log 2>&1

# 문제 시 자동 복구
*/5 * * * * cd /Users/yeongchang.jeon/workspace/ai-agent && source .venv/bin/activate && python3 system_monitor/system_monitor.py health || ./system_monitor/monitor.sh restart >> system_monitor/monitor.log 2>&1
```

## 테스트 결과

- ✅ 상태 확인: 모든 프로세스/컨테이너 상태 정확히 표시
- ✅ 헬스 체크: 문제 있는 서비스 정확히 감지
- ✅ 프로세스 제어: start/stop/restart 명령 정상 작동
- ✅ Docker 관리: 컨테이너 시작/중지 정상 작동
- ✅ 로깅: 모든 작업이 monitor.log에 기록됨

## 배포 준비 상태

✅ 프로덕션 준비 완료
- 모든 기능 구현 및 테스트 완료
- 종합 문서 작성 완료
- 에러 핸들링 구현 완료

## 다음 단계 (선택사항)

1. **자동 재시작 설정** - Cron 또는 LaunchAgent로 정기적 헬스 체크
2. **알림 시스템** - 서비스 장애 시 이메일/Slack 알림
3. **웹 대시보드** - 원격 모니터링 가능한 웹 UI
4. **성능 추적** - 장기 성능 데이터 수집 및 분석

