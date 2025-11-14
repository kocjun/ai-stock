# 🖥️ 시스템 프로세스 모니터링 및 관리 - 완벽 가이드

## 📋 목차

1. [개요](#개요)
2. [구성 요소](#구성-요소)
3. [설치 및 설정](#설치-및-설정)
4. [사용법](#사용법)
5. [대시보드](#대시보드)
6. [문제 해결](#문제-해결)
7. [자동화](#자동화)

---

## 개요

현재 AI 투자 시스템은 여러 백그라운드 프로세스와 Docker 컨테이너로 구성되어 있습니다:

### 모니터링 대상

**Python 백그라운드 프로세스:**
- 📊 **Price Scheduler**: 자동 가격 업데이트 (시간별)
- 📈 **Dashboard**: Dash 웹 대시보드 (포트 8050)
- 🤖 **Trading Crew**: AI 기반 일일 매매 (수동 실행)

**Docker 컨테이너:**
- 🐘 **PostgreSQL (investment_db)**: 투자 데이터베이스 (포트 5432)
- 🔄 **N8N**: 자동화 플랫폼 (포트 5678)

**외부 서비스:**
- 🧠 **Ollama**: 로컬 LLM 모델 (포트 11434)

---

## 구성 요소

### 1. `system_monitor.py` - 핵심 모니터링 엔진

```
기능:
├─ Python 프로세스 상태 확인
├─ Docker 컨테이너 상태 확인
├─ 서비스 포트 가용성 검사
├─ 프로세스 시작/중지/재시작
├─ 실시간 CPU/메모리 모니터링
└─ 로그 기록 및 PID 관리
```

### 2. `monitor.sh` - 편리한 셸 래퍼

```
기능:
├─ 모든 Python/Docker 명령 통합
├─ 색상 코드 상태 표시
├─ 한 번에 전체 시스템 제어
└─ 사용하기 쉬운 CLI
```

### 3. `processes.json` - 설정 파일

```
설정:
├─ 모니터링할 프로세스 정의
├─ Docker 컨테이너 설정
├─ 자동 재시작 옵션
└─ 리소스 제한 설정
```

### 4. `monitor.log` - 로그 파일

```
기록:
├─ 모든 시작/중지 이벤트
├─ 타임스탬프 포함
├─ 오류 및 경고
└─ 히스토리 추적
```

---

## 설치 및 설정

### 필수 요구사항

```bash
# Python 3.8+
python3 --version

# Docker
docker --version

# pip 패키지
pip install psutil
```

### 디렉토리 구조

```
ai-agent/
├── system_monitor/                    # 모니터링 시스템
│   ├── system_monitor.py              # 핵심 스크립트
│   ├── monitor.sh                     # 셸 래퍼
│   ├── processes.json                 # 설정 파일
│   ├── monitor.log                    # 로그 파일
│   ├── README.md                      # 상세 가이드
│   ├── QUICKSTART.md                  # 빠른 시작
│   └── *.pid                          # PID 파일 (자동)
│
├── paper_trading/
│   ├── price_scheduler.py             # 가격 스케줄러
│   ├── dashboard.py                   # 대시보드
│   └── trading_crew.py                # 매매 워크플로우
│
├── .venv/                             # Python 가상환경
└── .env                               # 환경 변수
```

### 초기 설정

```bash
# 1. 프로젝트 디렉토리 이동
cd /Users/yeongchang.jeon/workspace/ai-agent

# 2. 가상환경 활성화
source .venv/bin/activate

# 3. 필수 패키지 설치
pip install psutil

# 4. 모니터링 디렉토리 이동
cd system_monitor

# 5. 스크립트 실행 권한 부여
chmod +x monitor.sh

# 6. 설정 확인
cat processes.json
```

---

## 사용법

### 기본 명령어

#### 1. 상태 확인

```bash
# 모든 프로세스/컨테이너의 현재 상태 표시
./monitor.sh status

# 또는 Python 직접 실행
python3 system_monitor.py status
```

**출력 예:**
```
🖥️  시스템 프로세스 모니터링 대시보드
업데이트: 2025-10-30 21:55:11

📌 Python 백그라운드 프로세스
────────────────────────────────────────────
🟢 PRICE_SCHEDULER
   상태:      RUNNING
   PID:       12345
   메모리:    125.45 MB
   CPU:       2.3%
   업타임:    45분

🔴 DASHBOARD
   상태:      STOPPED

📦 Docker 컨테이너
────────────────────────────────────────────
🟢 N8N
   상태:      RUNNING
   업타임:    120분

🌐 서비스 가용성
────────────────────────────────────────────
✅ PostgreSQL      (:5432) - 온라인
✅ Ollama          (:11434) - 온라인
✅ N8N             (:5678) - 온라인
❌ Dashboard       (:8050) - 오프라인
```

#### 2. 프로세스 시작

```bash
# 모든 프로세스 시작
./monitor.sh start

# 특정 프로세스만 시작
python3 system_monitor.py start price_scheduler
python3 system_monitor.py start dashboard
```

#### 3. 프로세스 중지

```bash
# 모든 프로세스 중지
./monitor.sh stop

# 특정 프로세스만 중지
python3 system_monitor.py stop dashboard
```

#### 4. 프로세스 재시작 (문제 해결)

```bash
# 모든 프로세스 재시작
./monitor.sh restart

# 특정 프로세스만 재시작
python3 system_monitor.py restart price_scheduler
```

#### 5. 시스템 헬스 체크

```bash
# 전체 시스템 상태 점검
./monitor.sh health

# 출력 예 (정상)
✅ 모든 시스템이 정상입니다!

# 출력 예 (문제)
⚠️  2개의 문제 발견:

  • price_scheduler    (Python 프로세스): stopped
  • dashboard          (Python 프로세스): stopped
```

### Docker 컨테이너 관리

```bash
# PostgreSQL 시작
python3 system_monitor.py docker-start investment_db

# N8N 시작
python3 system_monitor.py docker-start n8n

# PostgreSQL 중지
python3 system_monitor.py docker-stop investment_db

# N8N 중지
python3 system_monitor.py docker-stop n8n
```

---

## 대시보드

### 상태 아이콘

| 아이콘 | 상태 | 설명 |
|--------|------|------|
| 🟢 | RUNNING | 프로세스 실행 중 |
| 🔴 | STOPPED | 프로세스 중지됨 |
| 🟠 | ERROR | 오류 발생 |
| 🟡 | UNKNOWN | 상태 불명확 |
| ❓ | NOT_FOUND | 컨테이너 없음 |
| ✅ | ONLINE | 서비스 온라인 |
| ❌ | OFFLINE | 서비스 오프라인 |

### 메트릭 설명

```
PID:       프로세스 ID (Process Identifier)
메모리:    RAM 사용량 (MB)
CPU:       CPU 점유율 (%)
업타임:    연속 실행 시간 (분)
```

### 포트 상태

```
데이터베이스:  :5432  (PostgreSQL)
LLM 모델:     :11434  (Ollama)
자동화:       :5678  (N8N)
대시보드:     :8050  (Dash)
```

---

## 문제 해결

### 문제 1: "Python 프로세스 not found"

```bash
# 확인 1: 프로세스가 있는지 확인
ps aux | grep python3

# 확인 2: PID 파일 확인
ls -la system_monitor/*.pid

# 해결: 프로세스 시작
python3 system_monitor.py start price_scheduler
```

### 문제 2: "Docker not found"

```bash
# 확인: Docker 설치 여부
docker --version

# 해결: Docker 설치
# Mac에서: https://docs.docker.com/docker-for-mac/install/
# Linux: sudo apt-get install docker-ce
```

### 문제 3: "Permission denied"

```bash
# 권한 문제 해결
chmod +x system_monitor/monitor.sh

# 또는 Python으로 직접 실행
python3 system_monitor/system_monitor.py status
```

### 문제 4: "Address already in use"

```bash
# 포트 점유 프로세스 확인
lsof -i :8050  # Dashboard 포트

# 프로세스 재시작
python3 system_monitor.py restart dashboard

# 또는 강제 종료
kill -9 $(lsof -t -i :8050)
```

### 문제 5: "Timeout"

```bash
# 느린 시스템에서 타임아웃 발생 시
# 다시 시도
./monitor.sh status

# 또는 Docker 상태만 확인
docker ps

# Python 상태만 확인
ps aux | grep -E "price_scheduler|dashboard"
```

### 문제 6: "모든 프로세스가 중지됨"

```bash
# 전체 시스템 재시작
./monitor.sh stop
sleep 5
./monitor.sh start

# 상태 확인
./monitor.sh health
```

---

## 자동화

### Cron 작업

```bash
# crontab 편집
crontab -e

# 예: 매 30분마다 헬스 체크
*/30 * * * * cd /Users/yeongchang.jeon/workspace/ai-agent && source .venv/bin/activate && python3 system_monitor/system_monitor.py health >> system_monitor/monitor.log 2>&1

# 예: 매일 오전 9시 상태 확인
0 9 * * * cd /Users/yeongchang.jeon/workspace/ai-agent && source .venv/bin/activate && ./system_monitor/monitor.sh status >> system_monitor/monitor.log 2>&1

# 예: 문제 시 자동 복구
*/5 * * * * cd /Users/yeongchang.jeon/workspace/ai-agent && source .venv/bin/activate && python3 system_monitor/system_monitor.py health || ./system_monitor/monitor.sh restart >> system_monitor/monitor.log 2>&1
```

### LaunchAgent (Mac)

1. 파일 생성: `~/Library/LaunchAgents/com.aiagent.monitor.plist`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.aiagent.monitor</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/yeongchang.jeon/workspace/ai-agent/system_monitor/monitor.sh</string>
        <string>start</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <dict>
        <key>SuccessfulExit</key>
        <true/>
        <key>Crashed</key>
        <true/>
    </dict>
</dict>
</plist>
```

2. 로드:
```bash
launchctl load ~/Library/LaunchAgents/com.aiagent.monitor.plist
```

### Bash Alias

`.zshrc` 또는 `.bashrc`에 추가:

```bash
# 모니터링 명령어 단축
alias mon='cd /Users/yeongchang.jeon/workspace/ai-agent/system_monitor && ./monitor.sh'
alias mon-status='mon status'
alias mon-health='mon health'
alias mon-restart='mon restart'
alias mon-start='mon start'
alias mon-stop='mon stop'
alias mon-log='tail -f /Users/yeongchang.jeon/workspace/ai-agent/system_monitor/monitor.log'

# 사용
mon status
mon health
mon restart
mon-log
```

---

## 모범 사례

### 일일 체크리스트

```bash
# 매일 아침 실행
./monitor.sh status        # 상태 확인
./monitor.sh health        # 헬스 체크

# 문제가 있으면
./monitor.sh restart       # 전체 재시작

# 대시보드 접속
open http://localhost:8050
```

### 주간 유지보수

```bash
# 일주일에 한 번 전체 시스템 재시작
./monitor.sh stop
sleep 5
./monitor.sh start
./monitor.sh health
```

### 월간 점검

```bash
# 로그 확인
tail -100 system_monitor/monitor.log

# 리소스 사용량 분석
top -b -n 1 | head -20

# 디스크 공간 확인
df -h
```

---

## 참고 사항

### 로그 파일 위치

```bash
# 실시간 로그 보기
tail -f system_monitor/monitor.log

# 특정 날짜 로그만 보기
grep "2025-10-30" system_monitor/monitor.log

# 오류만 보기
grep -i "error\|failed" system_monitor/monitor.log
```

### PID 파일 위치

```bash
system_monitor/
├── price_scheduler.pid    # Price Scheduler PID
├── dashboard.pid          # Dashboard PID
└── trading_crew.pid       # Trading Crew PID (없을 수도 있음)
```

### 설정 파일 수정

```bash
# 설정 파일 열기
cat system_monitor/processes.json

# 프로세스 추가 또는 수정
vi system_monitor/processes.json
```

---

## FAQ

**Q: 프로세스가 자동으로 재시작되나?**
A: 현재는 수동 재시작만 지원합니다. Cron/LaunchAgent로 자동화 가능합니다.

**Q: 원격에서도 모니터링 가능한가?**
A: 현재는 로컬만 지원합니다. SSH를 통해 원격 실행 가능합니다.

**Q: 알림(이메일/Slack)을 받을 수 있나?**
A: 현재는 로깅만 지원합니다. 향후 업데이트 예정입니다.

**Q: 과거 로그는 어디에?**
A: `system_monitor/monitor.log`에 누적됩니다.

---

## 다음 단계

1. **빠른 시작:** [QUICKSTART.md](system_monitor/QUICKSTART.md)
2. **상세 가이드:** [README.md](system_monitor/README.md)
3. **문제 해결:** 위의 "문제 해결" 섹션 참고

---

**최종 업데이트:** 2025-10-30
**상태:** ✅ 프로덕션 준비 완료
**버전:** 1.0

