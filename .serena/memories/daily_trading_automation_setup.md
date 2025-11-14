# 일일 자동 매매 스케줄러 설정 완료

**최종 수정**: 2025-10-30 22:07  
**상태**: ✅ 프로덕션 준비 완료

## 설정 개요

매일 평일 오전 9시에 **종목별 주도주 전략**을 기반으로 자동 매매를 실행하도록 설정했습니다.

## 완료된 작업

### 1. 실행 스크립트 생성
**파일**: `paper_trading/run_daily_trading.sh` (1438 bytes)

기능:
- 타임스탬프와 함께 매매 실행
- 성공/실패 상태 로깅
- 자동 에러 처리
- 로그: `paper_trading/trading_daily.log`

### 2. 프로세스 설정 업데이트
**파일**: `system_monitor/processes.json`

변경사항:
```json
{
  "name": "Trading Crew Workflow",
  "type": "python",
  "auto_restart": true,
  "command": "python paper_trading/trading_crew.py --strategy leader --top-n 10 --execute",
  "restart_interval_minutes": 1440,
  "max_memory_mb": 2000,
  "description": "종목별 주도주 전략 기반 일일 매매 워크플로우"
}
```

### 3. Cron 스케줄 설정
**실행 시간**: 평일(월-금) 오전 9시 정각

```bash
0 9 * * 1-5 /Users/yeongchang.jeon/workspace/ai-agent/paper_trading/run_daily_trading.sh >> /Users/yeongchang.jeon/workspace/ai-agent/paper_trading/trading_daily.log 2>&1
```

### 4. 설정 문서 작성
**파일**: `DAILY_TRADING_SETUP.md`

내용:
- 설정 상세 설명
- 검증 방법
- 모니터링 방법
- 트러블슈팅 가이드
- 주의사항 및 팁

## 현재 시스템 상태

```
✅ Python 프로세스
  🟢 PRICE_SCHEDULER    - RUNNING (PID: 34658)
  🟢 DASHBOARD          - RUNNING (PID: 34661)
  🔴 TRADING_CREW       - STOPPED (Cron으로 스케줄됨)

✅ Docker 컨테이너
  🟢 INVESTMENT_POSTGRES - RUNNING
  🟢 N8N                - RUNNING

✅ 서비스
  ✅ PostgreSQL (5432)
  ✅ Ollama (11434)
  ✅ N8N (5678)
  ✅ Dashboard (8050)
```

## 매매 전략 설정

### 선정 기준
- **전략**: leader (종목별 주도주)
- **개수**: 상위 10개 종목
- **실행**: --execute (실제 매매)

### 리더십 점수 구성
- 시가총액: 35% (시장 영향력)
- 거래대금: 25% (유동성)
- 모멘텀: 20% (상승세)
- 재무건전성: 15% (기초체력)
- 안정성: 5% (위험도)

## 확인 방법

### Cron 작업 확인
```bash
crontab -l | grep "run_daily_trading"
```

### 로그 실시간 확인
```bash
tail -f paper_trading/trading_daily.log
```

### 시스템 상태 확인
```bash
python3 system_monitor/system_monitor.py status
# 또는
./system_monitor/monitor.sh status
```

## 매매 전략 변경

leader 이외의 전략으로 변경하려면:

1. `system_monitor/processes.json` 수정
2. Cron 스케줄도 함께 수정 (`crontab -e`)

### 가능한 전략
- `--strategy leader` (현재)
- `--strategy ai`
- `--strategy sector`
- `--strategy hybrid`
- `--strategy ai-sector`

## 주의사항

### 시장 개장 시간
- 한국 증권시장: 09:00 개장
- Cron 설정: 09:00 (개장 직전)
- 필요시 09:30으로 변경 가능

### 메모리 관리
- 최대 허용: 2000MB
- 초과 시 자동 재시작

### 로그 정리
```bash
# 한 달 이상 된 로그 삭제
find paper_trading -name "trading_daily.log" -mtime +30 -delete
```

## 다음 단계 (선택사항)

1. 매매 성과 추적 대시보드 구축
2. 리더십 점수 가중치 최적화
3. 알림 시스템 (매매 완료/실패 시 알림)
4. 성과 분석 리포트 자동 생성

