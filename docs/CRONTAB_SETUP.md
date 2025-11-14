# Crontab 설정 가이드

AI 주식 분석 시스템의 완전한 crontab 설정

---

## 📋 전체 Crontab 설정

```bash
# crontab -e
```

아래 내용을 복사해서 붙여넣으세요:

```cron
# ========================================
# AI 에이전트 자동화 스케줄
# ========================================

# ----------------------------------------
# 데이터 수집
# ----------------------------------------
# 일간 데이터 수집: 매일 오후 6시 (18:00)
0 18 * * * cd /Users/yeongchang.jeon/workspace/ai-agent && ./run_daily_collection.sh >> /Users/yeongchang.jeon/workspace/ai-agent/logs/cron_daily.log 2>&1

# ----------------------------------------
# Paper Trading (로컬 LLM)
# ----------------------------------------
# 일일 Trading: 평일 오전 10시 (시장 개장 후)
0 10 * * 1-5 cd /Users/yeongchang.jeon/workspace/ai-agent && ./paper_trading/run_paper_trading.sh >> /Users/yeongchang.jeon/workspace/ai-agent/logs/cron_trading.log 2>&1

# ----------------------------------------
# 주간 분석 및 검증 (토요일)
# ----------------------------------------
# 레드팀 검증: 토요일 오전 6시 (OpenAI)
0 6 * * 6 cd /Users/yeongchang.jeon/workspace/ai-agent && ./paper_trading/run_redteam_validation.sh >> /Users/yeongchang.jeon/workspace/ai-agent/logs/cron_redteam.log 2>&1

# 주간 보고서: 토요일 오전 7시
0 7 * * 6 cd /Users/yeongchang.jeon/workspace/ai-agent && ./paper_trading/generate_weekly_report.sh >> /Users/yeongchang.jeon/workspace/ai-agent/logs/cron_report.log 2>&1

# 주간 분석: 토요일 오전 9시
0 9 * * 6 cd /Users/yeongchang.jeon/workspace/ai-agent && ./run_weekly_analysis.sh >> /Users/yeongchang.jeon/workspace/ai-agent/logs/cron_weekly.log 2>&1

# ========================================
```

---

## 📊 실행 순서 (시간순)

### 평일 (월-금)
```
10:00 │ Paper Trading 실행 (로컬 LLM)
18:00 │ 일간 데이터 수집
```

### 토요일
```
06:00 │ 레드팀 검증 (로컬 + OpenAI)
07:00 │ 주간 보고서 생성
09:00 │ 주간 분석 실행
```

### 일요일
```
(실행 없음 - 휴무)
```

---

## 🔧 설치 방법

### 1. 백업 (선택사항)
```bash
# 기존 crontab 백업
crontab -l > ~/crontab_backup_$(date +%Y%m%d).txt
```

### 2. Crontab 편집
```bash
# 편집 모드 진입
crontab -e

# vim 편집기:
# - i: 편집 모드
# - ESC: 명령 모드
# - :wq: 저장 후 종료
# - :q!: 저장 않고 종료
```

### 3. 설정 확인
```bash
# 설정된 crontab 확인
crontab -l

# Cron 로그 확인
tail -f /Users/yeongchang.jeon/workspace/ai-agent/logs/cron_*.log
```

---

## 📁 로그 파일 위치

모든 cron 작업의 로그가 별도로 관리됩니다:

```
logs/cron_daily.log      # 일간 데이터 수집
logs/cron_trading.log    # Paper Trading
logs/cron_redteam.log    # 레드팀 검증
logs/cron_report.log     # 주간 보고서
logs/cron_weekly.log     # 주간 분석
```

---

## 🧪 테스트

### 즉시 실행 테스트
각 작업을 수동으로 실행하여 테스트:

```bash
# 1. Paper Trading
./paper_trading/run_paper_trading.sh

# 2. 레드팀 검증
./paper_trading/run_redteam_validation.sh

# 3. 주간 보고서
./paper_trading/generate_weekly_report.sh

# 4. 데이터 수집
./run_daily_collection.sh

# 5. 주간 분석
./run_weekly_analysis.sh
```

### Cron 동작 확인
```bash
# 1분 후 실행되도록 임시 테스트
# 현재 시간 + 1분으로 설정
# 예: 지금이 14:30이면
# 31 14 * * * cd /Users/yeongchang.jeon/workspace/ai-agent && echo "Test" >> /tmp/cron_test.log

# 1분 후 확인
cat /tmp/cron_test.log
```

---

## 📊 주간 스케줄 시각화

```
      월   화   수   목   금   토   일
─────────────────────────────────────
10:00  🤖  🤖  🤖  🤖  🤖   -    -   Paper Trading (로컬)
18:00  📊  📊  📊  📊  📊   -    -   데이터 수집
06:00  -   -   -   -   -   🔴   -   레드팀 검증 (OpenAI)
07:00  -   -   -   -   -   📋   -   주간 보고서
09:00  -   -   -   -   -   📈   -   주간 분석
```

---

## ⚙️ 로그 로테이션

로그 파일이 너무 커지지 않도록 관리:

```bash
# 30일 이상 된 로그 자동 삭제 (선택사항)
# crontab에 추가:
0 0 * * 0 find /Users/yeongchang.jeon/workspace/ai-agent/logs -name "*.log" -mtime +30 -delete
```

또는 수동 정리:

```bash
# 로그 압축
cd /Users/yeongchang.jeon/workspace/ai-agent/logs
gzip cron_*.log

# 30일 이상 된 로그 삭제
find . -name "*.log.gz" -mtime +30 -delete
```

---

## 🔔 알림 설정

### 이메일 알림 (선택사항)

macOS에서 cron 실행 결과를 이메일로 받으려면:

```cron
# crontab 상단에 추가
MAILTO=your-email@example.com

# 또는 각 작업에 || mail 추가
0 10 * * 1-5 cd /path && ./script.sh || echo "Failed" | mail -s "Cron Error" you@email.com
```

### n8n 웹훅 알림 (이미 구현됨)

각 스크립트 내부에서 n8n으로 자동 알림 전송:
- Paper Trading 완료
- 레드팀 검증 완료
- 주간 보고서 완료

---

## 🐛 트러블슈팅

### 1. Cron이 실행되지 않을 때

```bash
# Cron 서비스 상태 확인 (macOS)
sudo launchctl list | grep cron

# 최근 Cron 로그 확인
log show --predicate 'process == "cron"' --last 1h --info
```

### 2. 경로 문제

```bash
# 절대 경로 사용 확인
which python3
which bash

# PATH 환경변수 확인
echo $PATH

# Cron 환경에서 PATH 설정
# crontab 상단에 추가:
PATH=/usr/local/bin:/usr/bin:/bin:/opt/homebrew/bin
```

### 3. 권한 문제

```bash
# 스크립트 실행 권한 확인
ls -l paper_trading/*.sh
ls -l *.sh

# 실행 권한 부여
chmod +x paper_trading/*.sh
chmod +x run_*.sh
```

### 4. Python 환경 문제

스크립트가 가상환경을 찾지 못하는 경우:

```bash
# 각 스크립트 확인
# .venv/bin/activate가 올바르게 있는지 확인

# 절대 경로로 수정
source /Users/yeongchang.jeon/workspace/ai-agent/.venv/bin/activate
```

---

## 📈 모니터링

### 실시간 로그 모니터링

```bash
# 모든 cron 로그 실시간 확인
tail -f logs/cron_*.log

# 특정 로그만
tail -f logs/cron_trading.log
```

### 실행 이력 확인

```bash
# 최근 실행된 cron 작업 확인
grep CRON /var/log/system.log | tail -20

# 특정 시간대 확인
log show --predicate 'eventMessage contains "cron"' --info --last 24h
```

### 성공/실패 확인

각 로그 파일에서:
```bash
# 성공 확인
grep "완료\|성공\|✅" logs/cron_trading.log

# 실패 확인
grep "실패\|에러\|❌" logs/cron_trading.log
```

---

## 💡 유용한 Tip

### 1. Cron 표현식 테스트

웹사이트 사용: https://crontab.guru/

```
0 10 * * 1-5  →  "At 10:00 on every day-of-week from Monday through Friday"
0 6 * * 6     →  "At 06:00 on Saturday"
```

### 2. 빠른 편집

```bash
# vim 대신 nano 사용
EDITOR=nano crontab -e

# 또는 환경변수 설정
export EDITOR=nano
crontab -e
```

### 3. 로그 파일 크기 확인

```bash
# 로그 파일 크기 확인
du -h logs/cron_*.log

# 큰 파일 찾기
find logs -name "*.log" -size +10M
```

---

## 🔄 업데이트 이력

- **2025-10-23**: 초기 버전
  - Paper Trading: 평일 10시
  - 레드팀 검증: 토요일 6시
  - 주간 보고서: 토요일 7시
  - 기존 데이터 수집/분석 통합

---

**작성일**: 2025-10-23
**버전**: 1.0
