# 이메일 알림 설정 가이드

Paper Trading 시스템은 매일 트레이딩 결과와 주간 레드팀 검증 결과를 이메일로 자동 전송합니다.

## 📧 이메일 알림 종류

### 1. 일일 Paper Trading 리포트
- **발송 시각**: 평일 오전 10시 트레이딩 완료 후
- **내용**:
  - 포트폴리오 현황 (총 자산, 현금, 보유 종목 수)
  - AI 추천 종목 및 비중
  - 당일 실행된 거래 내역

### 2. 주간 Red Team 검증 리포트
- **발송 시각**: 토요일 오전 6시 검증 완료 후
- **내용**:
  - 로컬 LLM vs OpenAI 일치율
  - 일치/불일치 종목 상세 비교
  - 품질 평가 및 권장 사항

## 🔧 Gmail 설정 (권장)

### 1. Gmail 앱 비밀번호 생성

Gmail에서 2단계 인증을 활성화한 후 앱 비밀번호를 생성해야 합니다.

1. Google 계정 설정 접속: https://myaccount.google.com/
2. **보안** 메뉴 선택
3. **2단계 인증** 활성화 (미활성화 상태라면)
4. **앱 비밀번호** 선택
5. 앱 선택: **메일**
6. 기기 선택: **기타 (맞춤 이름)** → "Paper Trading System" 입력
7. **생성** 클릭
8. 생성된 16자리 비밀번호 복사 (예: `abcd efgh ijkl mnop`)

### 2. .env 파일 설정

프로젝트 루트의 `.env` 파일을 편집합니다:

```bash
# ============================================================
# 이메일 설정 (일일 리포트 및 주간 검증 결과 전송)
# ============================================================
# SMTP 서버 설정 (Gmail 기준)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587

# 이메일 주소 설정
EMAIL_FROM=your-email@gmail.com      # 발신 이메일 주소
EMAIL_TO=your-email@gmail.com        # 수신 이메일 주소 (다른 주소 가능)

# Gmail 앱 비밀번호 (공백 제거)
SMTP_PASSWORD=abcdefghijklmnop
```

**주의사항**:
- `SMTP_PASSWORD`는 Gmail 로그인 비밀번호가 **아닙니다**
- 반드시 **앱 비밀번호**를 사용해야 합니다
- 앱 비밀번호 입력 시 **공백을 제거**하세요 (예: `abcd efgh ijkl mnop` → `abcdefghijklmnop`)

### 3. 설정 테스트

이메일 전송이 제대로 설정되었는지 테스트:

```bash
# 가상환경 활성화
source .venv/bin/activate

# 간단한 테스트 (Python에서)
python3 -c "
from core.utils.email_sender import send_email
send_email(
    subject='테스트 이메일',
    body_html='<h1>Paper Trading 이메일 설정 테스트</h1><p>이메일이 정상적으로 전송되었습니다.</p>'
)
"
```

성공 시 출력:
```
✅ 이메일 전송 완료: your-email@gmail.com
```

실패 시 출력:
```
❌ 이메일 전송 실패: [에러 메시지]
```

## 🔒 다른 이메일 서비스 사용

### Naver 메일

```bash
SMTP_SERVER=smtp.naver.com
SMTP_PORT=587
EMAIL_FROM=your-email@naver.com
EMAIL_TO=your-email@naver.com
SMTP_PASSWORD=your-naver-password
```

### Outlook / Hotmail

```bash
SMTP_SERVER=smtp-mail.outlook.com
SMTP_PORT=587
EMAIL_FROM=your-email@outlook.com
EMAIL_TO=your-email@outlook.com
SMTP_PASSWORD=your-outlook-password
```

### Daum 메일

```bash
SMTP_SERVER=smtp.daum.net
SMTP_PORT=465
EMAIL_FROM=your-email@daum.net
EMAIL_TO=your-email@daum.net
SMTP_PASSWORD=your-daum-password
```

## 📨 이메일 형식

### Paper Trading 일일 리포트

```
제목: [Paper Trading] 일일 리포트 - 2025-10-23

내용:
┌─────────────────────────────────────┐
│ 📊 Paper Trading 일일 리포트         │
│ 2025년 10월 23일 10:15              │
└─────────────────────────────────────┘

💼 포트폴리오 현황
┌──────────────┬──────────────┬──────────┐
│   총 자산     │    현금      │  보유종목 │
├──────────────┼──────────────┼──────────┤
│ 10,000,000원 │ 2,000,000원  │   3개    │
└──────────────┴──────────────┴──────────┘

🎯 AI 추천 종목 (3개)
┌─────────┬──────────────┬────────┐
│ 종목코드 │   종목명      │  비중  │
├─────────┼──────────────┼────────┤
│ 005930  │  삼성전자     │ 33.3% │
│ 000660  │  SK하이닉스   │ 33.3% │
│ 035720  │  카카오       │ 33.3% │
└─────────┴──────────────┴────────┘

🤖 AI 주식 투자 시스템 | Paper Trading Mode
```

### Red Team 주간 검증 리포트

```
제목: [Red Team] 주간 검증 리포트 - 2025-10-23

내용:
┌─────────────────────────────────────┐
│ 🔍 Red Team 검증 리포트              │
│ 2025년 10월 23일 06:15              │
└─────────────────────────────────────┘

┌─────────────────────────┐
│        80.0%           │
│     ✅ 우수             │
│ 로컬 LLM vs OpenAI 일치율│
└─────────────────────────┘

📊 상세 비교 결과

✅ 일치하는 종목 (2개)
005930, 000660

🔵 로컬 LLM만 추천 (1개)
035720

🔴 OpenAI만 추천 (0개)
없음

💡 권장 사항
📌 로컬 LLM과 OpenAI가 80% 이상 일치합니다.
   로컬 LLM 결과를 신뢰할 수 있습니다.

🤖 AI 주식 투자 시스템 | Red Team Validation
```

## ⚠️ 문제 해결

### 1. "이메일 전송 실패" 오류

**증상**: `❌ 이메일 전송 실패`

**원인 및 해결**:

1. **앱 비밀번호 오류**
   - Gmail 로그인 비밀번호가 아닌 **앱 비밀번호**를 사용했는지 확인
   - 앱 비밀번호에 공백이 없는지 확인

2. **2단계 인증 미활성화**
   - Gmail 2단계 인증을 활성화해야 앱 비밀번호 생성 가능
   - https://myaccount.google.com/security 에서 확인

3. **SMTP 서버/포트 오류**
   - Gmail: `smtp.gmail.com:587`
   - 다른 서비스는 해당 서비스의 SMTP 설정 확인

4. **방화벽 차단**
   - 포트 587 (또는 465) 아웃바운드 연결 허용 확인

### 2. ".env 파일의 이메일 설정을 확인하세요" 메시지

**증상**: 이메일 전송 시도 시 설정 불완전 메시지

**해결**:
```bash
# .env 파일에 다음 항목이 모두 설정되어 있는지 확인
EMAIL_FROM=your-email@gmail.com
EMAIL_TO=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

### 3. 이메일이 스팸으로 분류됨

**해결**:
1. 스팸 폴더 확인
2. 해당 이메일을 "스팸 아님"으로 표시
3. 발신자를 주소록에 추가

### 4. 이메일이 전송되지 않음 (오류 없음)

**원인**: 트레이딩 또는 검증이 실패하여 이메일 전송 단계에 도달하지 못함

**확인**:
```bash
# 로그 파일 확인
cat paper_trading/logs/trading_*.log | tail -50
cat paper_trading/logs/redteam/validation_*.log | tail -50
```

## 🔕 이메일 알림 비활성화

이메일 알림을 받고 싶지 않다면:

### 방법 1: .env에서 이메일 설정 제거

```bash
# .env 파일에서 다음 줄들을 주석 처리 또는 삭제
# EMAIL_FROM=...
# EMAIL_TO=...
# SMTP_PASSWORD=...
```

### 방법 2: 스크립트 수정

1. `paper_trading/run_paper_trading.sh` 편집
2. 이메일 전송 부분 주석 처리:

```bash
# # 이메일 전송 (성공 시에만)
# echo "" | tee -a "$LOG_FILE"
# echo "[이메일 전송]" | tee -a "$LOG_FILE"
# ...
```

3. `paper_trading/run_redteam_validation.sh`도 동일하게 수정

## 📚 관련 파일

- **이메일 유틸리티**: `core/utils/email_sender.py`
- **Paper Trading 스크립트**: `paper_trading/run_paper_trading.sh`
- **Red Team 검증 스크립트**: `paper_trading/run_redteam_validation.sh`
- **환경 설정**: `.env`

## 📞 추가 문의

이메일 설정 관련 문제가 계속되면:
1. 로그 파일 확인 (`paper_trading/logs/`)
2. Gmail 계정 보안 설정 재확인
3. 다른 이메일 서비스 시도
