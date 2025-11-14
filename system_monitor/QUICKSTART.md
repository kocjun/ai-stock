# 🚀 시스템 모니터링 - 빠른 시작 가이드

## ⚡ 1분 안에 시작하기

### 1단계: 상태 확인

```bash
cd /Users/yeongchang.jeon/workspace/ai-agent

# 방법 1: Python 직접 실행 (가상환경 필요)
source .venv/bin/activate
python3 system_monitor/system_monitor.py status

# 방법 2: 셸 스크립트 사용 (권장)
cd system_monitor
./monitor.sh status
```

### 2단계: 모든 프로세스 시작

```bash
./monitor.sh start
```

### 3단계: 헬스 체크

```bash
./monitor.sh health
```

---

## 🎯 자주 사용하는 명령어

### 상태 확인
```bash
./monitor.sh status
```

**출력:**
- 🟢 = 실행 중
- 🔴 = 중지됨
- ❌ = 오프라인
- ✅ = 서비스 온라인

### 프로세스 시작
```bash
# 모든 프로세스 시작
./monitor.sh start

# 특정 프로세스만 시작
python3 system_monitor.py start price_scheduler
python3 system_monitor.py start dashboard
```

### 프로세스 재시작 (문제 해결)
```bash
# 모든 프로세스 재시작
./monitor.sh restart

# 특정 프로세스만 재시작
python3 system_monitor.py restart price_scheduler
```

### 프로세스 중지
```bash
# 모든 프로세스 중지
./monitor.sh stop

# 특정 프로세스만 중지
python3 system_monitor.py stop dashboard
```

### 시스템 점검
```bash
./monitor.sh health
```

문제가 있으면:
```
⚠️  2개의 문제 발견:

  • price_scheduler    (Python 프로세스): stopped
  • dashboard          (Python 프로세스): stopped
```

---

## 🐳 Docker 컨테이너 관리

### 컨테이너 시작
```bash
# PostgreSQL 데이터베이스
python3 system_monitor.py docker-start investment_db

# N8N 자동화
python3 system_monitor.py docker-start n8n
```

### 컨테이너 중지
```bash
python3 system_monitor.py docker-stop investment_db
python3 system_monitor.py docker-stop n8n
```

---

## 📊 모니터링 대시보드 이해하기

```
🖥️  시스템 프로세스 모니터링 대시보드

📌 Python 백그라운드 프로세스
────────────────────────────────────────

🟢 PRICE_SCHEDULER
   상태:      RUNNING           👈 프로세스 상태
   PID:       12345             👈 프로세스 ID
   메모리:    125.45 MB         👈 메모리 사용량
   CPU:       2.3%              👈 CPU 사용률
   업타임:    45분              👈 실행 시간

📦 Docker 컨테이너
────────────────────────────────────────

🟢 N8N
   상태:      RUNNING
   업타임:    120분

🌐 서비스 가용성
────────────────────────────────────────

✅ PostgreSQL      (:5432) - 온라인
✅ Ollama          (:11434) - 온라인
✅ N8N             (:5678) - 온라인
❌ Dashboard       (:8050) - 오프라인    👈 문제: Dashboard 실행 필요
```

---

## 🔧 일반적인 문제 해결

### 문제 1: Dashboard가 오프라인 (❌)

```bash
# 대시보드 시작
python3 system_monitor.py start dashboard

# 또는 재시작
python3 system_monitor.py restart dashboard

# 상태 확인
./monitor.sh status
```

### 문제 2: Price Scheduler가 중지됨 (🔴)

```bash
# 스케줄러 재시작
python3 system_monitor.py restart price_scheduler

# 상태 확인
./monitor.sh health
```

### 문제 3: 모든 프로세스가 중지됨

```bash
# 전체 시스템 재시작
./monitor.sh restart

# 또는 개별 실행
./monitor.sh start
```

### 문제 4: Docker 컨테이너 접근 불가

```bash
# Docker 설치 확인
docker --version

# Docker 실행 확인
docker ps

# Docker 시작 (Mac)
open -a Docker
```

---

## 💡 일일 모니터링 루틴

### 매일 아침
```bash
# 1. 상태 확인
./monitor.sh status

# 2. 헬스 체크
./monitor.sh health

# 3. 문제가 있으면 재시작
./monitor.sh restart
```

### 주간 점검
```bash
# 전체 시스템 재시작 (유지보수)
./monitor.sh stop
sleep 5
./monitor.sh start
./monitor.sh health
```

---

## 🌐 포트 참고

| 서비스 | 포트 | URL | 상태 |
|--------|------|-----|------|
| PostgreSQL | 5432 | `localhost:5432` | ✅ 필수 |
| Ollama | 11434 | `localhost:11434` | ✅ 필수 |
| N8N | 5678 | `http://localhost:5678` | ✅ 자동화 |
| Dashboard | 8050 | `http://localhost:8050` | ⚡ 중요 |

---

## 📝 로그 확인

```bash
# 실시간 로그 보기
tail -f system_monitor/monitor.log

# 모든 로그 보기
cat system_monitor/monitor.log

# 최근 50줄
tail -50 system_monitor/monitor.log
```

---

## ✨ 자동화 설정 (선택사항)

### Mac: LaunchAgent로 자동 시작

1. 파일 생성:
```bash
nano ~/Library/LaunchAgents/com.aiagent.monitor.plist
```

2. 내용 추가:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
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
    <true/>
</dict>
</plist>
```

3. 활성화:
```bash
launchctl load ~/Library/LaunchAgents/com.aiagent.monitor.plist
```

### Cron: 정기적 헬스 체크

```bash
# crontab 편집
crontab -e

# 매 30분마다 헬스 체크
*/30 * * * * cd /Users/yeongchang.jeon/workspace/ai-agent && source .venv/bin/activate && python3 system_monitor/system_monitor.py health >> system_monitor/monitor.log 2>&1

# 매일 아침 9시에 상태 확인 및 문제 복구
0 9 * * * cd /Users/yeongchang.jeon/workspace/ai-agent && source .venv/bin/activate && python3 system_monitor/system_monitor.py health || ./system_monitor/monitor.sh restart >> system_monitor/monitor.log 2>&1
```

---

## 📞 추가 정보

- **상세 가이드:** [README.md](README.md)
- **설정 파일:** [processes.json](processes.json)
- **로그 파일:** `monitor.log`
- **메인 스크립트:** [system_monitor.py](system_monitor.py)
- **셸 래퍼:** [monitor.sh](monitor.sh)

---

## 🎓 팁과 트릭

### Alias 설정으로 빠른 실행

```bash
# .zshrc 또는 .bashrc에 추가
alias mon='cd /Users/yeongchang.jeon/workspace/ai-agent/system_monitor && ./monitor.sh'
alias mon-status='mon status'
alias mon-health='mon health'
alias mon-restart='mon restart'

# 사용
mon status
mon health
mon restart
```

### 한 줄로 확인하고 복구

```bash
./monitor.sh health || ./monitor.sh restart && ./monitor.sh status
```

### 모든 프로세스 상태를 JSON으로

```python
python3 -c "
import json
from system_monitor import SystemMonitor
m = SystemMonitor()
print(json.dumps(m.get_all_status(), indent=2))
"
```

---

**마지막 업데이트:** 2025-10-30
**다음 단계:** [상세 가이드](README.md) 읽기
