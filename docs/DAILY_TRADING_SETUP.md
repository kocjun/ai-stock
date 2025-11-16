# 📊 일일 자동 매매 설정 가이드

**최종 수정: 2025-10-30**
**상태: ✅ 설정 완료 및 검증됨**

---

## 📋 설정 개요

매일 오전 9시 평일에 **종목별 주도주 전략**을 기반으로 자동 매매를 실행합니다.

### 설정 구성요소
1. **실행 스크립트**: `paper_trading/run_daily_trading.sh`
2. **프로세스 설정**: `system_monitor/processes.json`
3. **Cron 스케줄**: 매일 평일 오전 9시 (월-금, 09:00)
4. **로그 기록**: `paper_trading/trading_daily.log`

---

## 🔧 상세 설정

### 1. 실행 스크립트
**파일**: `paper_trading/run_daily_trading.sh`

```bash
python3 paper_trading/trading_crew.py \
    --strategy leader \      # 주도주 전략 사용
    --top-n 10 \             # 상위 10개 종목 선정
    --execute                # 실제 매매 실행
```

**특징**:
- ✅ 타임스탬프와 함께 실행 기록
- ✅ 성공/실패 상태 로깅
- ✅ 자동 에러 처리

### 2. 프로세스 설정
**파일**: `system_monitor/processes.json`

```json
{
  "trading_crew": {
    "name": "Trading Crew Workflow",
    "type": "python",
    "auto_restart": true,
    "command": "python paper_trading/trading_crew.py --strategy leader --top-n 10 --execute",
    "restart_interval_minutes": 1440,
    "max_memory_mb": 2000,
    "description": "종목별 주도주 전략 기반 일일 매매 워크플로우"
  }
}
```

**설정값 의미**:
- `auto_restart: true` - 프로세스 종료 후 자동 재시작
- `restart_interval_minutes: 1440` - 24시간마다 재시작
- `max_memory_mb: 2000` - 최대 2GB 메모리 허용

### 3. Cron 스케줄
**실행 시간**: 평일(월-금) 오전 9시 정각

```bash
0 9 * * 1-5 /Users/yeongchang.jeon/workspace/ai-agent/paper_trading/run_daily_trading.sh >> /Users/yeongchang.jeon/workspace/ai-agent/paper_trading/trading_daily.log 2>&1
```

**Cron 표현식 분석**:
- `0` - 0분
- `9` - 9시 (오전)
- `*` - 매일
- `*` - 매월
- `1-5` - 평일 (월=1, 화=2, 수=3, 목=4, 금=5)

### 4. 로그 파일
**위치**: `paper_trading/trading_daily.log`

각 실행마다 다음 정보를 기록합니다:
```
========================================
시작 시간: 2025-10-30 09:00:01
========================================
[실행 로그 내용...]
✅ 매매 완료 (종료 코드: 0)
종료 시간: 2025-10-30 09:15:23
```

---

## ✅ 설정 확인 방법

### 1. Cron 작업 확인
```bash
crontab -l | grep "run_daily_trading"
```

**기대 출력**:
```
0 9 * * 1-5 /Users/yeongchang.jeon/workspace/ai-agent/paper_trading/run_daily_trading.sh >> ...
```

### 2. 프로세스 설정 확인
```bash
cd /Users/yeongchang.jeon/workspace/ai-agent
source .venv/bin/activate
python3 -c "import json; config = json.load(open('system_monitor/processes.json')); print(config['processes']['trading_crew'])"
```

### 3. 스크립트 문법 확인
```bash
bash -n paper_trading/run_daily_trading.sh
```

**기대 출력**: (오류 없음)

### 4. 수동 테스트 실행
```bash
# 실제 매매 없이 분석만 수행
cd /Users/yeongchang.jeon/workspace/ai-agent
source .venv/bin/activate
python3 paper_trading/trading_crew.py --strategy leader --top-n 10
```

---

## 📊 시스템 모니터링

### 실시간 상태 확인
```bash
cd /Users/yeongchang.jeon/workspace/ai-agent
source .venv/bin/activate
python3 system_monitor/system_monitor.py status
```

### 헬스 체크
```bash
./system_monitor/monitor.sh health
```

### 로그 확인
```bash
# 실시간 로그 보기
tail -f paper_trading/trading_daily.log

# 마지막 50줄 확인
tail -50 paper_trading/trading_daily.log

# 특정 날짜의 로그만 필터링
grep "2025-10-30" paper_trading/trading_daily.log
```

---

## 🔄 주도주 전략 파라미터

### `--strategy leader`
**의미**: 종목별 주도주 리더십 점수 기반 선정

**점수 구성** (총 100점):
- 시가총액: 35점 (시장 영향력)
- 거래대금: 25점 (유동성)
- 모멘텀: 20점 (상승세)
- 재무건전성: 15점 (기초체력)
- 안정성: 5점 (위험도)

### `--top-n 10`
**의미**: 리더십 스코어 상위 10개 종목 선정

### `--execute`
**의미**: 실제 매매 주문 생성 (분석 전용 아님)

---

## ⚠️ 주의사항

### 1. 시장 시간 고려
- ❌ 한국 증권시장은 09:00 개장
- ✅ Cron 설정된 09:00은 충분히 개장 전
- ⚠️ 필요시 09:30으로 변경 가능 (개장 30분 후)

**변경 방법**:
```bash
crontab -e
# 다음 줄을 찾아서:
# 0 9 * * 1-5 ...
# 다음처럼 변경:
# 30 9 * * 1-5 ...
```

### 2. 연결 실패 대비
- `auto_restart: true` 설정으로 자동 재시작
- 최대 30분 내에 자동 복구
- 수동 복구: `./monitor.sh restart trading_crew`

### 3. 메모리 관리
- 최대 허용 메모리: 2000MB
- 과도한 메모리 사용 시 자동 종료 및 재시작

### 4. 로그 관리
- 로그 파일은 계속 누적됨
- 정기적으로 정리 필요
  ```bash
  # 한 달 이상 된 로그 삭제
  find paper_trading -name "trading_daily.log" -mtime +30 -delete
  ```

---

## 🚀 매매 전략 변경

### 다른 전략으로 변경하기
**파일**: `system_monitor/processes.json`

```json
// AI 전략으로 변경
"command": "python paper_trading/trading_crew.py --strategy ai --top-n 10 --execute"

// Sector 전략으로 변경
"command": "python paper_trading/trading_crew.py --strategy sector --top-n 10 --execute"

// Hybrid 전략으로 변경
"command": "python paper_trading/trading_crew.py --strategy hybrid --top-n 10 --execute"
```

변경 후:
```bash
crontab -e  # Cron 스케줄도 함께 업데이트 필요
```

---

## 📈 성과 추적

### 일일 매매 기록 조회
```bash
# 최근 10개 매매
tail -100 paper_trading/trading_daily.log | grep "✅\|⚠️"

# 성공률 통계
grep "✅ 매매 완료" paper_trading/trading_daily.log | wc -l
```

### 포트폴리오 성과 확인
```bash
# 대시보드에서 실시간 확인
# http://localhost:8050
```

---

## 🔗 관련 문서

- [시스템 모니터링 가이드](SYSTEM_MONITORING.md)
- [주도주 전략 가이드](docs/LEADER_STRATEGY_QUICKSTART.md)
- [거래 팀(Trading Crew) 문서](docs/PHASE2_LEADER_STRATEGY.md)

---

## ✨ 설정 완료 체크리스트

- [x] `run_daily_trading.sh` 스크립트 생성
- [x] 스크립트에 실행 권한 설정
- [x] `processes.json`에 trading_crew 설정 업데이트
- [x] Cron 스케줄 등록 (평일 09:00)
- [x] 로그 파일 초기화
- [x] 설정 문법 검증
- [x] 문서 작성 완료

**상태**: ✅ **프로덕션 준비 완료**

---

## 📞 트러블슈팅

### Cron 작업이 실행되지 않음
```bash
# 1. Cron 데몬 확인
pgrep cron

# 2. 권한 확인
ls -la paper_trading/run_daily_trading.sh
# 기대: -rwxr-xr-x (실행 권한 있음)

# 3. 경로 확인
# Cron에 절대 경로 사용했는지 확인

# 4. 로그 확인
log stream --predicate 'process == "cron"' --level debug
```

### 스크립트 실행 오류
```bash
# 1. 스크립트 직접 실행
/Users/yeongchang.jeon/workspace/ai-agent/paper_trading/run_daily_trading.sh

# 2. 에러 로그 확인
tail -50 paper_trading/trading_daily.log
```

### 매매 주문이 생성되지 않음
```bash
# 1. 데이터베이스 연결 확인
python3 -c "from database import get_portfolio; print(get_portfolio())"

# 2. 가상 계좌 상태 확인
python3 -c "from database import query; print(query('SELECT * FROM virtual_accounts'))"

# 3. 주도주 리스트 조회
python3 paper_trading/leader_strategy.py
```

---

