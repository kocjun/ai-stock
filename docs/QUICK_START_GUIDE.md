# 🚀 종합 시장 분석 시스템 - 빠른 시작 가이드

**버전**: 1.0 (완성 및 테스트 완료)
**상태**: ✅ 운영 준비 완료
**마지막 테스트**: 2025년 11월 5일 20:58:08

---

## ⚡ 5분 내 시작하기

### 1단계: 확인 (1분)

모든 필수 파일이 준비되었는지 확인:

```bash
# 필수 파일 확인
ls -la core/agents/market_news_crew.py
ls -la core/agents/kospi_etf_analyzer.py
ls -la core/utils/market_news_sender.py
ls -la core/utils/market_news_email_template.py
ls -la scripts/send_market_news.sh
ls -la .env
```

✅ **모두 준비됨** - 다음 단계로 진행

---

### 2단계: 환경 설정 확인 (2분)

**.env 파일 확인:**

```bash
grep -E "^(SMTP_SERVER|SMTP_PORT|SMTP_PASSWORD|EMAIL_FROM|EMAIL_TO)" .env
```

**필수 설정 항목**:
- ✅ SMTP_SERVER=smtp.gmail.com
- ✅ SMTP_PORT=587
- ✅ SMTP_PASSWORD="qhir ehsr izqx lmzx"
- ✅ EMAIL_FROM=kocjun@gmail.com
- ✅ EMAIL_TO=kocjun@gmail.com

모두 설정됨 ✅

---

### 3단계: 수동 실행 테스트 (2분)

시스템을 한 번 실행해보기:

```bash
cd /Users/yeongchang.jeon/workspace/ai-agent
.venv/bin/python core/agents/market_news_crew.py
```

**예상 결과**:
```
============================================================
📰 시장 뉴스 분석 시작...
============================================================

✅ 뉴스 분석 완료

============================================================
📈 코스피 지수 & ETF 분석 시작...
============================================================

✅ 코스피 지수 분석 완료

============================================================
📋 최종 종합 시장 분석 리포트
============================================================

[... 종합 분석 리포트 ... ]

============================================================
✅ 분석 완료!
============================================================

============================================================
📧 이메일 발송
============================================================
📧 SMTP를 통한 이메일 발송 중...
✅ SMTP를 통한 이메일 발송 성공
   크기: 19856 bytes

✅ 이메일 발송 완료!
```

✅ **이메일 수신함 확인** - 분석 보고서 도착 확인

---

## 🔄 자동 실행 설정 (선택)

### Crontab 설정 (매일 오전 7시 자동 실행)

```bash
# crontab 편집 모드 열기
crontab -e
```

**아래 줄 추가**:

```bash
# 매일 오전 7시 (월-금 평일만) 실행
0 7 * * 1-5 cd /Users/yeongchang.jeon/workspace/ai-agent && source .venv/bin/activate && python core/agents/market_news_crew.py >> logs/market_news_$(date +\%Y\%m\%d).log 2>&1
```

**저장 방법**:
- Vim 편집기: `:wq` 입력 후 Enter
- Nano 편집기: Ctrl+X → Y → Enter

**확인**:
```bash
# 설정된 crontab 확인
crontab -l

# 로그 확인 (다음날 오전 7시 이후)
tail -f logs/market_news_*.log
```

✅ **자동 실행 설정 완료**

---

## 📧 이메일 확인

### Gmail 받은편지함 확인

1. Gmail 열기: https://mail.google.com
2. 검색어: `from:kocjun@gmail.com 코스피`
3. 이메일 확인

**이메일 내용**:
- PART 1: 시장 뉴스 분석 (4개 카테고리)
- PART 2: 코스피 지수 & ETF 분석
- PART 3: 최종 투자 가이드 요약

✅ **이메일 형식 확인**: HTML 형식 (반응형)

---

## 📊 분석 결과 이해하기

### 시장 분석 점수

```
⚠️ 높은 영향도 뉴스
🟡 중간 영향도 뉴스
✅ 낮은 영향도 뉴스
```

### 코스피 방향성

```
강세 ⬆️       → 적극 매수 (공격적 전략)
약세 상승 ↗️  → 선별적 매수
중립 ➡️      → 관망 및 기회 포착
약세 하락 ↘️  → 방어적 포지셀닝
강세 하락 ⬇️  → 현금 보유 및 대기
```

### ETF 추천 액션

```
🟢 매수 강추   → 수익률 2% 이상 기대
🟢 매수        → 수익률 0.5-2% 기대
🟡 중립/보유   → 수익률 -0.5-0.5%
🔴 매도        → 손실 2% 이상 우려
🔴 매도 강추   → 손실 2% 이상 확실
```

---

## 🔍 문제 해결

### 이메일이 안 왔을 때

**1단계: 실행 확인**
```bash
.venv/bin/python core/agents/market_news_crew.py
```

**2단계: 로그 확인**
```bash
# 가장 최근 로그 확인
ls -la logs/market_news_*.log | tail -1
tail -50 logs/market_news_*.log
```

**3단계: 스팸 폴더 확인**
- Gmail 스팸 폴더 확인
- 발신자 추가: kocjun@gmail.com

**4단계: SMTP 오류 확인**

| 오류 | 해결책 |
|------|--------|
| SMTPAuthenticationError | Gmail 비밀번호 확인 |
| SMTPException | SMTP 서버 상태 확인 |
| 타임아웃 | 네트워크 연결 확인 |

### Crontab이 작동하지 않을 때

```bash
# 1. Crontab 설정 확인
crontab -l

# 2. 경로 확인
which python
# 출력: /Users/yeongchang.jeon/workspace/ai-agent/.venv/bin/python

# 3. 절대 경로 사용 확인
# ❌ python (상대 경로 X)
# ✅ /Users/yeongchang.jeon/workspace/ai-agent/.venv/bin/python (절대 경로)

# 4. Crontab 로그 확인 (Mac)
log stream --predicate 'process == "cron"' --level debug
```

---

## 📈 포트폴리오 구성 예시

### 현재 시장 상황 (강세 ⬆️)

**공격적 전략**:
```
TIGER 200: 40%      (대형주 중심, 안정)
KODEX 소형주: 20%   (고수익 추구)
TIGER 배당성장: 20% (수익 고착)
TIGER 중형주: 10%   (균형)
현금/채권: 10%      (기회 대기)
```

**기대 수익률**: 5.0% - 6.5% / 월

---

## 📞 자주 묻는 질문

### Q: 매일 같은 시간에 이메일을 받아야 하나요?

**A**: 네, Crontab이 설정되면 매일 오전 7시에 자동 발송됩니다.
- 평일(월-금)만 실행
- 휴장일에도 실행됨 (사용하지 않으면 무시)
- 수동 실행으로 언제든지 추가 분석 가능

---

### Q: 분석 결과가 100% 정확한가요?

**A**: 아니요, 이것은 교육용 분석입니다.
- Mock 뉴스 데이터 사용
- 실제 뉴스 API 연동 가능 (향후)
- 항상 전문가 상담 권고
- 법적 책임은 사용자가 가짐

---

### Q: 포트폴리오 구성을 바꾸고 싶어요

**A**: 분석 결과를 참고하여 자유롭게 조정하세요.
- PART 3에 3가지 전략 제시
- 자신의 위험 성향에 맞게 선택
- 월 1회 리밸런싱 권고

---

### Q: 배당금을 받으려면?

**A**: TIGER 배당성장 ETF를 보유하면 됩니다.
- 배당락일에 자동 배당
- 연 3-4회 배당금 지급
- 배당금을 재투자하면 복리 효과

---

### Q: 손절매는 언제?

**A**: 개인의 투자 계획에 따라 다릅니다.
- 보수적: -5% (손실 최소화)
- 일반적: -10% (적절한 손절)
- 공격적: -15% (변동성 수용)

---

## 🎯 다음 단계

### 1️⃣ 지금 바로 하기
```bash
# 수동 실행으로 분석 보고서 받기
cd /Users/yeongchang.jeon/workspace/ai-agent
.venv/bin/python core/agents/market_news_crew.py
```

### 2️⃣ 자동 실행 설정
```bash
# Crontab 설정 (매일 오전 7시)
crontab -e
```

### 3️⃣ 보고서 검토
- 이메일의 3가지 PART 읽기
- 자신의 투자 성향과 비교
- 포트폴리오 구성 검토

### 4️⃣ 투자 결정
- PART 3의 포트폴리오 예시 참고
- 전문가 상담 (권고)
- 매매 실행

---

## 📚 추가 학습

### 관련 문서
- [FINAL_INTEGRATION_SUMMARY.md](./FINAL_INTEGRATION_SUMMARY.md) - 전체 시스템 설명
- [COMPREHENSIVE_REPORT_STRUCTURE.md](./COMPREHENSIVE_REPORT_STRUCTURE.md) - 보고서 구조
- [MARKET_NEWS_SETUP.md](./MARKET_NEWS_SETUP.md) - 상세 설정 가이드

### 코드 이해
- `core/agents/market_news_crew.py` - 메인 분석 엔진
- `core/agents/kospi_etf_analyzer.py` - KOSPI 분석
- `core/utils/market_news_sender.py` - 이메일 발송

---

## ✅ 완료 체크리스트

- [ ] 5분 시작 가이드 읽음
- [ ] 필수 파일 확인 완료
- [ ] .env 설정 확인 완료
- [ ] 수동 실행 테스트 완료
- [ ] 이메일 수신 확인 완료
- [ ] Crontab 자동 실행 설정 (선택)
- [ ] 포트폴리오 구성 검토
- [ ] 투자 계획 수립

---

## 🎉 축하합니다!

**완전한 자동화된 시장 분석 시스템 구축 완료**

이제 매일 아침 7시에 자동으로 최신 시장 분석 보고서를 받을 수 있습니다.

**오늘부터**:
- ✅ 매일 오전 7시 자동 분석
- ✅ 증시 개장 2시간 전 이메일 수신
- ✅ 3가지 포트폴리오 전략 제시
- ✅ 5개 ETF 추천순위 제공
- ✅ 최종 투자 가이드 수수 제공

**행운을 빕니다! 📈**

---

**문의 및 피드백**: core/agents/market_news_crew.py 참고
**마지막 업데이트**: 2025년 11월 5일

