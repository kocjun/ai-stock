# 📅 시스템 운영 스케줄

AI 주식 분석 시스템의 자동화 실행 일정

---

## 🕐 일일 스케줄 (평일)

### 오전 10:00 - Paper Trading 실행

```
시간: 평일(월-금) 오전 10시
LLM: Ollama gpt-oss:120b (로컬)
비용: 무료
소요 시간: 약 10-20분
```

**실행 내용:**
1. 포트폴리오 현재가 업데이트
2. 손절/익절 체크
3. AI 종목 분석 (로컬 LLM)
4. 매수/매도 판단
5. 일일 스냅샷 저장

**선택 이유:**
- 시장 개장(09:00) 후 1시간 경과
- 초기 시장 데이터 안정화
- 당일 투자 전략 수립 가능

---

## 📊 주간 스케줄 (토요일)

### 오전 06:00 - 레드팀 검증

```
시간: 매주 토요일 오전 6시
LLM: Ollama + OpenAI (레드팀)
비용: ~$0.02-0.05
소요 시간: 약 20-30분
```

**실행 내용:**
1. 로컬 LLM으로 분석 실행
2. OpenAI로 동일 분석 실행
3. 결과 비교 및 일치율 계산
4. 교정 레포트 생성
5. n8n 알림 전송

**선택 이유:**
- 주말 시간 활용 (시장 휴무)
- 다음 주 전략 사전 검증
- 시스템 리소스 충분

### 오전 07:00 - 주간 보고서

```
시간: 매주 토요일 오전 7시
소요 시간: 약 5분
```

**실행 내용:**
1. 주간 성과 집계
2. 포트폴리오 분석
3. 거래 통계
4. 보고서 생성 및 전송

**선택 이유:**
- 레드팀 검증 완료 후 실행
- 한 주 성과 종합 리뷰
- 다음 주 전략 수립 자료

---

## 📈 시각화 스케줄

```
월요일 ~ 금요일 (평일)
─────────────────────────
09:00 │ 📊 시장 개장
10:00 │ 🤖 Paper Trading 실행 (로컬 LLM)
      │ └─ 포트폴리오 업데이트
      │ └─ AI 종목 분석
      │ └─ 매매 판단
15:30 │ 📊 시장 마감


토요일 (주간 검증)
─────────────────────────
06:00 │ 🔴 레드팀 검증 시작
      │ ├─ 로컬 LLM 실행
      │ ├─ OpenAI 실행
      │ ├─ 결과 비교
      │ └─ 알림 전송
07:00 │ 📊 주간 보고서 생성
      │ └─ 성과 분석
      │ └─ 보고서 전송


일요일
─────────────────────────
(휴무 - 스케줄 없음)
```

---

## 🔧 Cron 설정

### 설치 방법

```bash
# crontab 편집
crontab -e

# 아래 내용 추가
```

### Cron 설정 코드

```cron
# ============================================================
# AI 주식 분석 시스템 자동화 스케줄
# ============================================================

# 일일 Paper Trading (로컬 LLM) - 평일 오전 10시
0 10 * * 1-5 cd /Users/yeongchang.jeon/workspace/ai-agent && ./paper_trading/run_paper_trading.sh

# 주간 레드팀 검증 (OpenAI) - 토요일 오전 6시
0 6 * * 6 cd /Users/yeongchang.jeon/workspace/ai-agent && ./paper_trading/run_redteam_validation.sh

# 주간 보고서 생성 - 토요일 오전 7시
0 7 * * 6 cd /Users/yeongchang.jeon/workspace/ai-agent && ./paper_trading/generate_weekly_report.sh

# ============================================================
```

### Cron 시간 형식

```
분 시 일 월 요일
│ │ │  │  │
│ │ │  │  └─── 요일 (0-7, 0=일요일, 1=월요일, ..., 6=토요일)
│ │ │  └─────── 월 (1-12)
│ │ └────────── 일 (1-31)
│ └──────────── 시 (0-23)
└────────────── 분 (0-59)

* = 모든 값
*/n = n마다
1-5 = 1부터 5까지
1,3,5 = 1, 3, 5만
```

---

## 📋 로그 파일 위치

### Paper Trading 로그
```
paper_trading/logs/trading_YYYYMMDD_HHMMSS.log
paper_trading/logs/trading_workflow_YYYYMMDD_HHMMSS.json
```

### 레드팀 검증 로그
```
paper_trading/logs/redteam/validation_YYYYMMDD_HHMMSS.log
paper_trading/logs/redteam/validation_YYYYMMDD_HHMMSS.json
```

### 주간 보고서
```
paper_trading/reports/weekly_report_YYYYMMDD.md
```

---

## 🧪 수동 실행

자동화 전에 수동으로 테스트할 수 있습니다:

### Paper Trading
```bash
# 직접 실행
./paper_trading/run_paper_trading.sh

# 또는
python paper_trading/trading_crew.py --save-log
```

### 레드팀 검증
```bash
# 직접 실행
./paper_trading/run_redteam_validation.sh

# 또는
python paper_trading/redteam_validator.py
```

### 주간 보고서
```bash
# 직접 실행
./paper_trading/generate_weekly_report.sh

# 또는
python paper_trading/performance_reporter.py --type weekly --save-db --send-n8n
```

---

## 📊 월간 실행 요약

| 항목 | 횟수 | LLM | 비용 |
|------|------|-----|------|
| 일일 Trading | 20-22회 | 로컬 | 무료 |
| 레드팀 검증 | 4회 | 로컬+OpenAI | ~$0.10 |
| 주간 보고서 | 4회 | - | 무료 |
| **월 합계** | **28-30회** | - | **~$0.10** |

---

## ⚙️ 스케줄 관리

### Cron 상태 확인
```bash
# 현재 설정된 cron 확인
crontab -l

# Cron 서비스 상태 (macOS)
sudo launchctl list | grep cron
```

### Cron 로그 확인 (macOS)
```bash
# 시스템 로그
log show --predicate 'process == "cron"' --last 1h

# Cron 실행 이력
grep CRON /var/log/system.log
```

### Cron 수정
```bash
# 편집
crontab -e

# 삭제
crontab -r

# 백업
crontab -l > crontab_backup.txt

# 복원
crontab crontab_backup.txt
```

---

## 🔔 알림 설정

### n8n 웹훅 알림

각 작업 완료 시 n8n으로 알림이 전송됩니다:

1. **Paper Trading 완료**
   - 분석 결과 요약
   - 추천 종목
   - 포트폴리오 현황

2. **레드팀 검증 완료**
   - 일치율
   - 차이점 분석
   - 권장사항

3. **주간 보고서 완료**
   - 성과 요약
   - 거래 통계
   - 주간 수익률

---

## ⚠️ 주의사항

### 1. 시간대 설정
- Cron은 시스템 시간대 사용
- 한국 시간(KST) 기준 확인 필요

### 2. 시스템 리소스
- gpt-oss:120b는 65GB RAM 필요
- 실행 중 다른 작업 자제

### 3. 네트워크
- Ollama 서버 실행 상태 확인
- OpenAI API 접근 가능 확인

### 4. 권한
- 스크립트 실행 권한 확인
  ```bash
  chmod +x paper_trading/*.sh
  ```

---

## 🔧 트러블슈팅

### Cron이 실행되지 않을 때

```bash
# 1. 스크립트 권한 확인
ls -l paper_trading/*.sh

# 2. 절대 경로 사용 확인
which python3

# 3. 환경변수 로드 확인
# 스크립트 시작 부분에 추가:
# source ~/.zshrc

# 4. 로그 파일 확인
tail -100 paper_trading/logs/*.log
```

### 수동 실행은 되지만 Cron은 안 될 때

```bash
# Cron 환경에서 테스트
* * * * * /bin/bash -c "cd /Users/yeongchang.jeon/workspace/ai-agent && env > /tmp/cron-env.txt"

# 환경변수 비교
cat /tmp/cron-env.txt
```

---

**작성일**: 2025-10-23
**버전**: 1.0
**마지막 수정**: 평일 오전 10시 / 토요일 오전 6시로 변경
