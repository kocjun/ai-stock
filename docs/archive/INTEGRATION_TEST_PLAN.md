# 📊 AI 분석 에이전트 + Paper Trading 통합 테스트 계획

**작성일**: 2025-10-22
**버전**: 1.0
**목적**: 주식 분석 AI 에이전트와 Paper Trading 시스템의 End-to-End 통합 검증

---

## 🎯 테스트 목표

주식 분석 AI 에이전트(`integrated_crew`)가 포트폴리오를 분석하고, Paper Trading 시스템(`trading_crew`)이 이를 실제 가상 투자로 실행하는 전체 워크플로를 검증합니다.

### 검증 범위
1. ✅ AI 분석 파이프라인 (4단계 에이전트)
2. ✅ 분석 결과 → 매매 실행 변환
3. ✅ Paper Trading 시뮬레이션
4. ✅ 포트폴리오 관리 (손절/익절)
5. ✅ 실시간 대시보드 모니터링
6. ✅ 성과 보고서 생성

---

## 📋 시스템 구조

```
┌─────────────────────────────────────────────────────────────┐
│                    AI 분석 파이프라인                          │
│  (core/agents/integrated_crew.py)                           │
│                                                              │
│  Data Curator → Screening → Risk Manager → Portfolio        │
│  (데이터 수집)    (종목 선정)   (리스크 분석)    (포트폴리오)  │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
         [추천 종목 리스트 + 투자 비중]
                       │
                       ▼
┌──────────────────────┴──────────────────────────────────────┐
│              Paper Trading 실행기                            │
│  (paper_trading/trading_crew.py)                           │
│                                                              │
│  1. 추천 파싱 → 2. 매수 계획 → 3. 매매 실행 → 4. 포트폴리오  │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────┴──────────────────────────────────────┐
│                 PostgreSQL Database                          │
│  - virtual_accounts (계좌)                                   │
│  - virtual_trades (거래)                                     │
│  - virtual_portfolio (포지션)                                │
│  - virtual_portfolio_history (히스토리)                      │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────┴──────────────────────────────────────┐
│            실시간 웹 대시보드                                 │
│  (paper_trading/dashboard.py)                               │
│  - 포트폴리오 현황 / 성과 분석 / 거래 내역                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 🧪 테스트 시나리오

### Phase 1: 사전 준비 및 환경 검증 (5분)

#### 1.1 서비스 상태 확인
```bash
# Docker 서비스 확인
docker ps | grep -E "postgres|n8n"

# Ollama 서버 확인
curl http://localhost:11434/api/tags

# 데이터베이스 연결 확인
python core/utils/db_utils.py
```

**예상 결과**:
- ✅ `investment_postgres` 컨테이너 실행 중
- ✅ `n8n` 컨테이너 실행 중
- ✅ Ollama 서버 응답 (llama3.1:8b 모델 존재)
- ✅ PostgreSQL 연결 성공

#### 1.2 데이터 수집 상태 확인
```bash
python -c "
from core.utils.db_utils import get_db_connection
conn = get_db_connection()
cur = conn.cursor()
cur.execute('SELECT COUNT(*) FROM stocks')
print(f'종목 수: {cur.fetchone()[0]}')
cur.execute('SELECT MAX(date) FROM prices')
print(f'최신 가격 날짜: {cur.fetchone()[0]}')
cur.close()
conn.close()
"
```

**예상 결과**:
- ✅ 종목 수: 100개 이상
- ✅ 최신 가격: 최근 3일 이내

**문제 발생 시**:
```bash
# 데이터 재수집
python collect_data.py
```

#### 1.3 가상 계좌 초기 상태 확인
```bash
# 포트폴리오 조회
python paper_trading/paper_trading.py portfolio --account-id 1
```

**예상 결과**:
```
계좌 ID: 1
계좌명: AI 투자 시뮬레이션 #1
현금 잔고: 10,000,000원
보유 종목: 0개
총 자산: 10,000,000원
```

---

### Phase 2: AI 분석 전용 테스트 (DRY RUN) (10-15분)

**목적**: 실제 매매 없이 AI 분석 결과만 확인

#### 2.1 소규모 분석 실행
```bash
# 테스트 실행 (5개 종목 분석 → 3개 선정)
python paper_trading/trading_crew.py \
    --market KOSPI \
    --limit 5 \
    --top-n 3 \
    --cash-reserve 0.3 \
    --save-log
```

**예상 출력**:
```
================================================================================
📅 일일 자동 매매 워크플로 - 2025-10-22 21:30:00
================================================================================

Step 1/5: 포트폴리오 업데이트
✓ 포트폴리오 업데이트 완료

Step 2/5: 손절/익절 체크
✓ 매도 권장 종목: 0개

Step 3/5: AI 분석 실행
[Data Curator] 데이터 수집 중...
[Screening Analyst] 종목 스크리닝 중...
[Risk Manager] 리스크 분석 중...
[Portfolio Planner] 포트폴리오 구성 중...
✓ AI 분석 완료 (소요 시간: 8분)

추천 종목:
- 005930 (삼성전자): 33.3% (AI 분석 추천)
- 000660 (SK하이닉스): 33.3% (AI 분석 추천)
- 035420 (NAVER): 33.3% (AI 분석 추천)

Step 4/5: 매수 실행
[DRY RUN] 실제 매매 실행 안 함

Step 5/5: 일일 스냅샷 저장
✓ 스냅샷 저장 완료
```

#### 2.2 검증 포인트
- [ ] AI 에이전트 4단계 모두 실행되는가?
- [ ] 추천 종목이 3개인가?
- [ ] 종목 코드가 6자리 숫자 형식인가?
- [ ] 비중 합계가 100%에 가까운가?
- [ ] 소요 시간이 15분 이내인가?

---

### Phase 3: 실제 매매 시뮬레이션 (LIVE TEST) (10분)

**목적**: 실제 Paper Trading 매수 실행 및 포트폴리오 구성

#### 3.1 초기 포트폴리오 구성 (매수)
```bash
# 실제 매매 실행 (--execute 플래그 추가)
python paper_trading/trading_crew.py \
    --market KOSPI \
    --limit 10 \
    --top-n 5 \
    --cash-reserve 0.2 \
    --stop-loss -10.0 \
    --take-profit 20.0 \
    --execute \
    --save-log
```

**예상 결과**:
```
Step 4/5: 매수 실행
============================================================
초기 포트폴리오 구성
============================================================
총 5개 종목 매수 예정

📊 005930: 15주 @ 70,000원 = 1,050,000원
   ✅ 매수 체결: 1,050,158원

📊 000660: 8주 @ 120,000원 = 960,000원
   ✅ 매수 체결: 960,144원

...

============================================================
매수 완료: 5/5건
총 투자 금액: 8,000,000원
============================================================
```

#### 3.2 포트폴리오 확인
```bash
# CLI로 확인
python paper_trading/paper_trading.py portfolio --account-id 1
```

**예상 결과**:
```
계좌 ID: 1
계좌명: AI 투자 시뮬레이션 #1
현금 잔고: 2,000,000원 (20%)
주식 평가액: 8,000,000원 (80%)
총 자산: 10,000,000원

보유 종목 (5개):
1. 삼성전자 (005930): 15주 ...
2. SK하이닉스 (000660): 8주 ...
...
```

#### 3.3 거래 내역 확인
```bash
python paper_trading/portfolio_manager.py trades --account-id 1 --limit 10
```

**예상 결과**:
- ✅ 매수 거래 5건 기록
- ✅ 거래 일시, 종목, 수량, 가격 정확

#### 3.4 일일 스냅샷 저장
```bash
python paper_trading/portfolio_manager.py snapshot --account-id 1
```

---

### Phase 4: 대시보드 모니터링 (5분)

#### 4.1 대시보드 실행
```bash
./paper_trading/run_dashboard.sh
```

**접속**: http://localhost:8050

#### 4.2 확인 사항
- [ ] **포트폴리오 현황**
  - [ ] 총 자산: 약 1,000만원
  - [ ] 현금 잔고: 약 200만원
  - [ ] 주식 평가액: 약 800만원
  - [ ] 보유 종목: 5개

- [ ] **보유 종목 테이블**
  - [ ] 종목명, 수량, 평단가, 현재가 표시
  - [ ] 손익률 계산 정확

- [ ] **포트폴리오 비중 파이 차트**
  - [ ] 5개 종목 색상 구분
  - [ ] 비중 합계 100%

- [ ] **성과 분석**
  - [ ] 수익률: 0% (초기)
  - [ ] 거래 횟수: 5건

- [ ] **거래 내역**
  - [ ] 매수 5건 표시
  - [ ] 필터링 동작

- [ ] **자동 새로고침**
  - [ ] 30초마다 업데이트
  - [ ] 마지막 업데이트 시간 표시

---

### Phase 5: 손절/익절 시뮬레이션 (5분)

#### 5.1 포트폴리오 업데이트
```bash
# 최신 가격 반영 (실제 시장 가격)
python paper_trading/paper_trading.py update --account-id 1
```

#### 5.2 손절/익절 체크
```bash
python paper_trading/portfolio_manager.py check-exit \
    --account-id 1 \
    --stop-loss -10.0 \
    --take-profit 20.0
```

**예상 출력**:
```
손절/익절 체크 결과:

손절 권장 (0개):
(없음)

익절 권장 (0개):
(없음)
```

**시나리오 테스트** (선택사항):
```bash
# 수동으로 특정 종목 매도하여 손익 기록
python paper_trading/paper_trading.py sell \
    --code 005930 \
    --quantity 5 \
    --reason "테스트 매도"
```

---

### Phase 6: 전체 워크플로 재실행 (10분)

**목적**: 기존 포트폴리오가 있는 상태에서 리밸런싱 테스트

#### 6.1 재실행
```bash
python paper_trading/trading_crew.py \
    --market KOSPI \
    --limit 10 \
    --top-n 5 \
    --execute \
    --save-log
```

**예상 동작**:
1. ✅ 기존 포지션 업데이트
2. ✅ 손절/익절 체크 (조건 충족 시 자동 매도)
3. ✅ AI 재분석 (새로운 추천)
4. ✅ 추가 매수 또는 비중 조정
5. ✅ 스냅샷 저장

**검증**:
- [ ] 기존 5개 종목 유지 또는 변경
- [ ] 현금 잔고 변화 기록
- [ ] 거래 내역 증가

---

### Phase 7: 성과 보고서 생성 (5분)

#### 7.1 주간 보고서 생성
```bash
python paper_trading/performance_reporter.py \
    --type weekly \
    --output reports/integration_test_report.md \
    --save-db
```

#### 7.2 보고서 확인
```bash
cat reports/integration_test_report.md
```

**예상 내용**:
```markdown
# 페이퍼 트레이딩 주간 성과 보고서

## 📊 자산 현황
- 초기 자금: 10,000,000원
- 현재 자산: 10,000,000원
- 총 수익: 0원 (0.00%)

## 📈 성과 지표
| 지표 | 값 |
|------|-----|
| 수익률 | 0.00% |
| Sharpe Ratio | 0.00 |
| MDD | 0.00% |
| 변동성 | 0.00% |

## 💼 현재 포트폴리오
| 종목명 | 수량 | 평단가 | 현재가 | 손익률 |
|--------|------|--------|--------|--------|
| 삼성전자 | 15 | 70,000 | 70,000 | 0.00% |
...

## 📋 거래 통계
- 총 거래: 5건 (매수 5, 매도 0)
- 승률: N/A
```

---

### Phase 8: 자동화 스크립트 테스트 (5분)

#### 8.1 일일 자동 실행 스크립트
```bash
# 분석만 (DRY RUN)
./paper_trading/run_paper_trading.sh
```

**로그 확인**:
```bash
tail -100 paper_trading/logs/trading_*.log
```

**검증**:
- [ ] 스크립트 정상 실행
- [ ] 로그 파일 생성
- [ ] 오류 없음

#### 8.2 주간 보고서 스크립트
```bash
./paper_trading/generate_weekly_report.sh
```

---

## ✅ 검증 체크리스트

### 필수 검증 항목

#### AI 분석 파이프라인
- [ ] Data Curator: 데이터 수집 완료
- [ ] Screening Analyst: 종목 선정 완료 (3-5개)
- [ ] Risk Manager: 리스크 분석 완료
- [ ] Portfolio Planner: 포트폴리오 구성 완료
- [ ] 총 소요 시간: < 15분

#### Paper Trading 실행
- [ ] 추천 종목 파싱 성공 (6자리 코드)
- [ ] 매수 수량 계산 정확
- [ ] 매수 체결 성공 (5/5건)
- [ ] 포트폴리오 업데이트
- [ ] 현금 잔고 감소 확인

#### 데이터베이스 기록
- [ ] `virtual_trades`: 거래 5건 기록
- [ ] `virtual_portfolio`: 포지션 5개 생성
- [ ] `virtual_portfolio_history`: 스냅샷 1개 이상
- [ ] 데이터 정합성 (잔고 = 초기자금 - 투자금액)

#### 대시보드 표시
- [ ] 포트폴리오 현황 정확
- [ ] 보유 종목 5개 표시
- [ ] 차트 렌더링 정상
- [ ] 거래 내역 5건 표시
- [ ] 실시간 업데이트 작동 (30초)

### 성능 검증
- [ ] AI 분석 소요 시간: **< 15분** (10개 종목 기준)
- [ ] 매매 체결 시간: **< 1초/종목**
- [ ] 대시보드 로딩: **< 3초**
- [ ] 전체 워크플로: **< 20분**

---

## 🐛 트러블슈팅

### 문제 1: Ollama 토큰 제한
**증상**: `CrewAI rate limit exceeded` 또는 느린 응답

**해결**:
```bash
# 분석 종목 수 축소
python paper_trading/trading_crew.py --limit 5 --top-n 3

# 또는 Ollama 재시작
brew services restart ollama
```

### 문제 2: 종목 코드 파싱 실패
**증상**: "포트폴리오 추천 정보를 찾을 수 없습니다"

**원인**: Crew 출력 포맷 변경

**해결**:
1. 로그 확인:
   ```bash
   tail -200 paper_trading/logs/trading_*.log
   ```
2. 파싱 로직 검토 (`trading_crew.py:parse_portfolio_recommendations`)
3. 정규식 패턴 조정

### 문제 3: 가격 정보 없음
**증상**: "종목 [코드]의 가격 정보를 찾을 수 없습니다"

**해결**:
```bash
# 최신 가격 데이터 수집
python collect_data.py

# 특정 종목 확인
python -c "
from core.utils.db_utils import get_db_connection
conn = get_db_connection()
cur = conn.cursor()
cur.execute('SELECT * FROM prices WHERE code=%s ORDER BY date DESC LIMIT 1', ('005930',))
print(cur.fetchone())
"
```

### 문제 4: 잔고 부족
**증상**: "잔고가 부족합니다 (현재: XXX원, 필요: YYY원)"

**해결**:
```bash
# 현금 보유 비율 증가
python paper_trading/trading_crew.py --cash-reserve 0.3

# 또는 선정 종목 수 감소
python paper_trading/trading_crew.py --top-n 3
```

### 문제 5: 대시보드 접속 불가
**증상**: `Connection refused` 또는 빈 화면

**해결**:
```bash
# 프로세스 확인
ps aux | grep dashboard.py

# 포트 확인
lsof -i :8050

# 재시작
pkill -f dashboard.py
./paper_trading/run_dashboard.sh
```

---

## 📊 성공 기준

### Minimum Viable Test (최소 성공 기준)
✅ AI 분석 완료 (추천 종목 3개 이상)
✅ Paper Trading 매수 1건 이상 성공
✅ 대시보드에 포트폴리오 표시

### Full Success (완전 성공)
✅ AI 분석 완료 (10개 분석, 5개 선정)
✅ Paper Trading 매수 5건 모두 성공
✅ 포트폴리오 업데이트 및 스냅샷 저장
✅ 대시보드 실시간 모니터링
✅ 손절/익절 체크 작동
✅ 성과 보고서 생성
✅ 자동화 스크립트 정상 작동

---

## 📝 테스트 결과 기록

### 실행 정보
- **일시**: YYYY-MM-DD HH:MM
- **테스터**: [이름]
- **환경**: macOS / Python 3.11 / Ollama llama3.1:8b

### Phase별 결과

#### Phase 1: 사전 준비 (목표: 5분)
- [ ] Pass / [ ] Fail - 서비스 상태 확인
- [ ] Pass / [ ] Fail - 데이터 수집 확인
- [ ] Pass / [ ] Fail - 계좌 초기 상태 확인
- 소요 시간: ___ 분
- 비고: ___

#### Phase 2: AI 분석 DRY RUN (목표: 10-15분)
- [ ] Pass / [ ] Fail - 분석 파이프라인 실행
- 소요 시간: ___ 분
- 추천 종목: [코드1, 코드2, 코드3]
- 비고: ___

#### Phase 3: Paper Trading LIVE (목표: 10분)
- [ ] Pass / [ ] Fail - 매수 실행
- 성공 건수: ___ / 5
- 투자 금액: ___원
- 현금 잔고: ___원
- 비고: ___

#### Phase 4: 대시보드 (목표: 5분)
- [ ] Pass / [ ] Fail - 대시보드 표시
- [ ] Pass / [ ] Fail - 포트폴리오 정확성
- [ ] Pass / [ ] Fail - 차트 렌더링
- 비고: ___

#### Phase 5: 손절/익절 (목표: 5분)
- [ ] Pass / [ ] Fail - 체크 기능 작동
- 손절 권장: ___ 개
- 익절 권장: ___ 개
- 비고: ___

#### Phase 6: 재실행 (목표: 10분)
- [ ] Pass / [ ] Fail - 워크플로 재실행
- [ ] Pass / [ ] Fail - 리밸런싱 동작
- 비고: ___

#### Phase 7: 보고서 (목표: 5분)
- [ ] Pass / [ ] Fail - 보고서 생성
- [ ] Pass / [ ] Fail - 내용 정확성
- 비고: ___

#### Phase 8: 자동화 (목표: 5분)
- [ ] Pass / [ ] Fail - 스크립트 실행
- [ ] Pass / [ ] Fail - 로그 생성
- 비고: ___

### 종합 평가
- [ ] Minimum Viable Test 통과
- [ ] Full Success 달성
- **총 소요 시간**: ___ 분
- **성공률**: ___ % (통과한 Phase / 8)

### 발견된 이슈
1. ___
2. ___

### 개선 제안
1. ___
2. ___

---

## 🚀 다음 단계 (테스트 통과 후)

### 1. 프로덕션 배포
- [ ] Cron 자동화 설정
  ```bash
  # 평일 18:30 자동 실행
  30 18 * * 1-5 /path/to/run_paper_trading.sh

  # 주간 보고서 (토요일 10:00)
  0 10 * * 6 /path/to/generate_weekly_report.sh
  ```

### 2. n8n 워크플로 통합
- [ ] 분석 결과 → 슬랙 알림
- [ ] 손절/익절 발생 → 이메일 알림
- [ ] 주간 보고서 → n8n 전송

### 3. 모니터링 및 최적화
- [ ] 일일 성과 추적
- [ ] AI 분석 정확도 평가
- [ ] 파라미터 튜닝 (손절/익절 기준, 현금 비율)

### 4. 고도화
- [ ] 멀티 전략 테스트 (보수적/공격적)
- [ ] 벤치마크 대비 성과 비교
- [ ] 백테스팅 시스템 구축

---

**문서 작성일**: 2025-10-22
**최종 수정일**: 2025-10-22
**작성자**: AI Assistant
**버전**: 1.0
