# 🖥️ 시스템 프로세스 모니터링 및 관리 도구

현재 실행 중인 모든 백그라운드 프로세스(Python, Docker)의 상태를 한눈에 확인하고 관리할 수 있는 통합 모니터링 시스템입니다.

## 📋 기능

### 1. **상태 모니터링** 📊
- Python 백그라운드 프로세스 (Price Scheduler, Dashboard, Trading Crew)
- Docker 컨테이너 (PostgreSQL, N8N)
- 외부 서비스 포트 (Ollama, N8N, Dashboard 등)
- 실시간 CPU, 메모리, 업타임 정보

### 2. **프로세스 관리** 🔧
- 프로세스 시작/중지/재시작
- Docker 컨테이너 제어
- 자동 PID 관리
- 프로세스 상태 자동 감지

### 3. **헬스 체크** 🏥
- 시스템 전체 상태 점검
- 문제 항목 자동 식별
- 상세 로깅

### 4. **로그 기록** 📝
- 모든 작업 기록
- 타임스탬프 포함
- 히스토리 추적

---

## 🚀 빠른 시작

### 설치

```bash
cd /Users/yeongchang.jeon/workspace/ai-agent/system_monitor

# 스크립트 실행 권한 부여
chmod +x monitor.sh
```

### 기본 사용

```bash
# 1️⃣ 상태 확인 (대시보드)
./monitor.sh status
# 또는
python3 system_monitor.py status

# 2️⃣ 모든 프로세스 시작
./monitor.sh start

# 3️⃣ 시스템 상태 점검
./monitor.sh health

# 4️⃣ 모든 프로세스 중지
./monitor.sh stop
```

---

## 📖 상세 사용법

### Python 프로세스 관리

#### 상태 확인
```bash
python3 system_monitor.py status
```

**출력 예:**
```
🖥️  시스템 프로세스 모니터링 대시보드
업데이트: 2025-10-30 21:53:00

📌 Python 백그라운드 프로세스
────────────────────────────────────────────

🟢 PRICE_SCHEDULER
   상태:      RUNNING
   PID:       12345
   메모리:    125.45 MB
   CPU:       2.3%
   업타임:    45분
```

#### 프로세스 시작
```bash
python3 system_monitor.py start <process_name>
```

사용 가능한 프로세스:
- `price_scheduler` - 가격 업데이트 스케줄러
- `dashboard` - Dash 대시보드
- `trading_crew` - 매매 워크플로우 (수동 실행)

**예:**
```bash
python3 system_monitor.py start price_scheduler
python3 system_monitor.py start dashboard
```

#### 프로세스 재시작
```bash
python3 system_monitor.py restart <process_name>
```

**예:**
```bash
python3 system_monitor.py restart dashboard
```

#### 프로세스 중지
```bash
python3 system_monitor.py stop <process_name>
```

---

### Docker 컨테이너 관리

#### Docker 컨테이너 시작
```bash
python3 system_monitor.py docker-start <container_name>
```

사용 가능한 컨테이너:
- `investment_db` - PostgreSQL 데이터베이스
- `n8n` - N8N 자동화 플랫폼

**예:**
```bash
python3 system_monitor.py docker-start investment_db
python3 system_monitor.py docker-start n8n
```

#### Docker 컨테이너 중지
```bash
python3 system_monitor.py docker-stop <container_name>
```

---

### 시스템 헬스 체크

```bash
python3 system_monitor.py health
```

**결과:**
- ✅ **정상**: 모든 시스템이 실행 중
- ⚠️ **문제**: 중지된 프로세스나 서비스 나열

**예출력:**
```
🏥 시스템 상태 점검 중...

⚠️  2개의 문제 발견:

  • price_scheduler    (Python 프로세스): stopped
  • n8n               (Docker): not_found
```

---

## 🛠️ 통합 셸 스크립트 사용

`monitor.sh`는 Python 스크립트를 래핑하는 편리한 인터페이스입니다.

### 사용법

```bash
./monitor.sh <command>
```

### 사용 가능한 명령어

| 명령어 | 설명 |
|--------|------|
| `status` | 상태 대시보드 표시 |
| `start` | 모든 프로세스/컨테이너 시작 |
| `stop` | 모든 프로세스/컨테이너 중지 |
| `restart` | 모든 프로세스/컨테이너 재시작 |
| `health` | 시스템 상태 점검 |
| `setup` | 초기 설정 |

### 예시

```bash
# 상태 확인
./monitor.sh status

# 전체 시작
./monitor.sh start

# 전체 재시작
./monitor.sh restart

# 전체 중지
./monitor.sh stop

# 헬스 체크
./monitor.sh health
```

---

## 📊 모니터링 대시보드

### 표시 항목

#### 1. Python 백그라운드 프로세스
```
🟢 PRICE_SCHEDULER
   상태:      RUNNING
   PID:       12345
   메모리:    125.45 MB
   CPU:       2.3%
   업타임:    45분
```

**상태 아이콘:**
- 🟢 `running` - 프로세스 실행 중
- 🔴 `stopped` - 프로세스 중지됨
- 🟠 `error` - 오류 발생
- 🟡 `unknown` - 상태 불명확

#### 2. Docker 컨테이너
```
🐳 INVESTMENT_DB
   상태:      RUNNING
   업타임:    120분
```

#### 3. 서비스 가용성
```
✅ PostgreSQL      (:5432) - 온라인
✅ Ollama          (:11434) - 온라인
✅ N8N             (:5678) - 온라인
✅ Dashboard       (:8050) - 온라인
```

---

## 📁 파일 구조

```
system_monitor/
├── system_monitor.py          # 메인 모니터링 스크립트
├── monitor.sh                 # 셸 래퍼 스크립트
├── processes.json             # 프로세스 설정 파일
├── monitor.log                # 모니터링 로그 (자동 생성)
├── *.pid                       # PID 파일 (자동 생성)
└── README.md                  # 이 문서
```

---

## ⚙️ 설정

### processes.json

프로세스 설정 파일로서 모니터링할 프로세스와 Docker 컨테이너를 정의합니다.

```json
{
  "processes": {
    "price_scheduler": {
      "name": "Price Updater Scheduler",
      "type": "python",
      "auto_restart": true,
      "command": "python paper_trading/price_scheduler.py --schedule hourly"
    }
  },
  "docker_containers": {
    "investment_db": {
      "name": "investment_db",
      "type": "database",
      "port": 5432,
      "auto_restart": true
    }
  }
}
```

### 커스터마이징

프로세스를 추가하거나 수정하려면 `processes.json`을 편집하세요.

```json
"your_process": {
  "name": "Your Process Name",
  "type": "python",
  "auto_restart": true,
  "command": "python your_script.py",
  "restart_interval_minutes": 30,
  "max_memory_mb": 500
}
```

---

## 📝 로깅

모든 작업은 `monitor.log`에 기록됩니다.

### 로그 확인

```bash
# 최근 로그 보기
tail -f system_monitor/monitor.log

# 모든 로그 보기
cat system_monitor/monitor.log
```

### 로그 형식

```
[2025-10-30 21:51:16] Price Scheduler 시작됨 (PID: 12345)
[2025-10-30 21:52:00] Dashboard 재시작됨 (PID: 12346)
[2025-10-30 21:53:00] investment_db 시작됨
```

---

## 🔄 자동 재시작

현재는 모니터링만 지원하며, 자동 재시작 기능은 cron 또는 systemd로 구현 가능합니다.

### Cron으로 정기적 헬스 체크

```bash
# crontab 편집
crontab -e

# 매 5분마다 상태 확인
*/5 * * * * cd /path/to/ai-agent && python3 system_monitor/system_monitor.py health >> system_monitor/monitor.log 2>&1
```

### Systemd 서비스 (선택사항)

향후 systemd 서비스 파일을 작성하여 자동 관리 가능합니다.

---

## 🚨 문제 해결

### 1. "PID 파일을 찾을 수 없습니다"

**원인:** 프로세스가 아직 시작되지 않음

**해결:**
```bash
python3 system_monitor.py start <process_name>
```

### 2. "Docker가 설치되지 않았습니다"

**원인:** Docker가 설치되지 않음 또는 실행 중이 아님

**해결:**
```bash
# Docker 설치 확인
docker --version

# Docker 시작 (Mac)
open -a Docker

# Docker 시작 (Linux)
sudo systemctl start docker
```

### 3. "프로세스를 찾을 수 없습니다"

**원인:** 프로세스가 이미 종료됨

**해결:**
```bash
python3 system_monitor.py start <process_name>
```

### 4. 포트 충돌

**증상:** "Address already in use"

**확인:**
```bash
lsof -i :<port_number>
```

**해결:**
```bash
python3 system_monitor.py restart <process_name>
```

---

## 📊 사용 예시

### 시나리오 1: 일일 모니터링

```bash
# 매일 아침 상태 확인
./monitor.sh status

# 문제가 있으면 자동 복구
./monitor.sh health && echo "정상" || ./monitor.sh restart
```

### 시나리오 2: 전체 시스템 재시작

```bash
# 모든 프로세스 재시작 (유지보수 시)
./monitor.sh stop
sleep 5
./monitor.sh start
./monitor.sh health
```

### 시나리오 3: 특정 프로세스 문제 해결

```bash
# 대시보드 문제 진단
python3 system_monitor.py status | grep DASHBOARD

# 대시보드 재시작
python3 system_monitor.py restart dashboard

# 상태 재확인
python3 system_monitor.py health
```

---

## 🎯 주요 포트

| 서비스 | 포트 | URL |
|--------|------|-----|
| PostgreSQL | 5432 | `localhost:5432` |
| Ollama | 11434 | `localhost:11434` |
| N8N | 5678 | `http://localhost:5678` |
| Dashboard | 8050 | `http://localhost:8050` |

---

## 📞 참고

- **Python 스크립트:** `system_monitor.py` - 핵심 모니터링 로직
- **셸 래퍼:** `monitor.sh` - 편리한 명령어 인터페이스
- **설정 파일:** `processes.json` - 프로세스 정의
- **로그 파일:** `monitor.log` - 작업 히스토리

---

## ✨ 향후 개선사항

- [ ] Slack/이메일 알림
- [ ] 웹 기반 대시보드
- [ ] 자동 재시작 기능
- [ ] 성능 메트릭 그래프
- [ ] 데이터베이스 백업 모니터링
- [ ] 시스템 리소스 모니터링 (디스크, 네트워크)

---

**작성일:** 2025-10-30
**버전:** 1.0
**상태:** ✅ 프로덕션 준비 완료
