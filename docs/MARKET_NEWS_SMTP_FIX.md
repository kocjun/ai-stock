# 시장 뉴스 이메일 발송 - SMTP 직접 발송 방식 (N8N 독립)

## 문제 상황

처음에 시장 뉴스 시스템은 N8N 웹훅을 통해 이메일을 발송하도록 설계되었습니다:

```
Python 분석 → N8N 웹훅 → 이메일 발송
```

그러나 N8N 웹훅 endpoint가 등록되지 않아 **404 Not Found** 오류가 발생했습니다:

```
❌ N8N 발송 실패: 404 Client Error: Not Found for url:
http://localhost:5678/webhook/report-webhook
```

**오류 원인:**
- N8N 워크플로우가 아직 N8N UI에서 import/create되지 않음
- 웹훅이 "active" 상태가 아니어야 함
- 매번 N8N 워크플로우를 수동으로 관리해야 함

## 해결 방안

N8N에 의존하지 않고 **Python의 표준 SMTP 라이브러리를 사용**하여 직접 이메일을 발송하도록 변경했습니다:

```
Python 분석 → SMTP 직접 발송 → 이메일
```

## 구현 상세

### 1. 새로운 SMTP 이메일 발송 함수 추가

**파일:** `core/utils/market_news_sender.py`

- `send_market_news_via_smtp()`: SMTP를 사용한 직접 이메일 발송
  - Gmail SMTP 서버를 이용한 표준 SMTP 인증
  - HTML 이메일 지원 (MIME multipart)
  - 환경 변수에서 SMTP 설정 읽기

```python
def send_market_news_via_smtp(
    report: str,
    recipient_email: Optional[str] = None,
    sender_email: Optional[str] = None,
    smtp_server: Optional[str] = None,
    smtp_port: Optional[int] = None,
    smtp_password: Optional[str] = None
) -> bool:
    """SMTP를 이용한 직접 이메일 발송 (N8N 불필요)"""
    # SMTP 연결, TLS 활성화, 인증, 발송
```

### 2. 우선순위 기반 이메일 발송

`send_market_news_email()` 함수가 이제 다음 순서로 시도합니다:

1. **SMTP 우선** (기본값): Gmail SMTP를 통한 직접 발송
2. **N8N 폴백** (옵션): SMTP 실패 시 N8N 웹훅 시도

```python
def send_market_news_email(
    report: str,
    webhook_url: Optional[str] = None,
    recipient_email: Optional[str] = None,
    use_smtp: bool = True  # ← 기본값: True
) -> bool:
```

### 3. market_news_crew.py에 통합

Python 스크립트가 분석 완료 후 자동으로 SMTP로 이메일을 발송합니다:

```python
# 이메일 발송 시도
try:
    from core.utils.market_news_sender import send_market_news_email
    success = send_market_news_email(result["report"], use_smtp=True)
    if success:
        print("\n✅ 이메일 발송 완료!")
    else:
        print("\n⚠️  이메일 발송 실패 (분석은 완료됨)")
except Exception as e:
    print(f"\n⚠️  이메일 발송 모듈 로드 실패: {e}")
```

## 필요한 환경 변수

### SMTP 설정 (필수)

```bash
# Gmail SMTP 서버
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_PASSWORD="구글 앱 비밀번호"  # 2FA 활성화 시 필요

# 발송자 이메일
EMAIL_FROM=your-email@gmail.com

# 수신자 이메일
REPORT_EMAIL_RECIPIENT=recipient@example.com
EMAIL_TO=recipient@example.com  # 대체 변수명
```

### N8N 설정 (선택사항)

N8N을 폴백으로 사용하려면:

```bash
N8N_WEBHOOK_URL=http://localhost:5678/webhook/report-webhook
```

## 테스트 결과

### 테스트 실행

```bash
$ bash scripts/send_market_news.sh
```

### 출력 결과

```
[2025-11-05 20:37:40] ✅ 가상환경 확인됨
[2025-11-05 20:37:40] ✅ SMTP_SERVER 설정됨: smtp.gmail.com
[2025-11-05 20:37:40] ✅ 발송자 이메일 설정됨
[2025-11-05 20:37:40] ✅ 수신자 이메일 설정됨
[2025-11-05 20:37:40] ✅ SMTP_PASSWORD 설정됨
[2025-11-05 20:37:44] ✅ 뉴스 분석 및 이메일 발송 완료
```

### 이메일 발송 로그

```
📧 SMTP를 통한 이메일 발송 중...
   발송자: kocjun@gmail.com
   수신자: kocjun@gmail.com
   SMTP 서버: smtp.gmail.com:587
✅ SMTP를 통한 이메일 발송 성공
   크기: 14775 bytes
```

## 장점

### 1. N8N 독립성
- N8N 워크플로우 설정/관리 불필요
- N8N 다운타임에 영향 없음
- 간단한 설정으로 바로 작동

### 2. 신뢰성
- Python 표준 라이브러리 사용
- 에러 처리 강화
- 재시도 로직 추가 가능

### 3. 비용 절감
- Gmail 계정으로 무한 이메일 발송
- N8N Pro 구독 불필요 (선택사항)
- AWS SES, SendGrid 등 다른 SMTP 서버로 쉽게 전환 가능

### 4. 자동화 단순화
```bash
# Crontab: 평일 오전 7시 자동 실행
0 7 * * 1-5 cd /path/to/ai-agent && bash scripts/send_market_news.sh
```

## 문제 해결

### 이메일이 오지 않음

1. **환경 변수 확인**
   ```bash
   echo $SMTP_SERVER
   echo $EMAIL_FROM
   echo $REPORT_EMAIL_RECIPIENT
   ```

2. **SMTP 비밀번호 확인** (Gmail 2FA 활성화 필요)
   - Google 계정 → 보안 → App 비밀번호
   - 생성된 비밀번호를 SMTP_PASSWORD로 설정

3. **로그 확인**
   ```bash
   tail -50 logs/market_news_*.log
   ```

4. **수동 테스트**
   ```bash
   python core/utils/market_news_sender.py
   ```

### "SMTP 인증 실패" 오류

Gmail 2FA 활성화 필요:

1. Google 계정 → 보안
2. 2단계 인증 활성화
3. App 비밀번호 생성 (Gmail 앱)
4. 생성된 비밀번호를 SMTP_PASSWORD로 사용

```bash
export SMTP_PASSWORD="생성된_16자리_비밀번호"
```

### "SMTP 타임아웃" 오류

- 방화벽에서 587 포트 열려있는지 확인
- 다른 SMTP 서버 시도:
  ```bash
  # AWS SES
  SMTP_SERVER=email-smtp.us-east-1.amazonaws.com
  SMTP_PORT=587

  # SendGrid
  SMTP_SERVER=smtp.sendgrid.net
  SMTP_PORT=587
  ```

## N8N 폴백 설정 (선택사항)

SMTP 발송 실패 시 N8N으로 자동 전환하려면:

1. N8N에서 웹훅 워크플로우 import
2. 워크플로우 활성화
3. N8N_WEBHOOK_URL 환경 변수 설정

```bash
export N8N_WEBHOOK_URL="http://localhost:5678/webhook/report-webhook"
```

그러면 자동으로 SMTP → N8N 순서로 시도합니다.

## 다음 단계

### 1. Crontab 자동화 설정

```bash
# 평일 오전 7시 자동 실행
crontab -e

# 추가:
0 7 * * 1-5 cd /Users/yeongchang.jeon/workspace/ai-agent && \
    bash scripts/send_market_news.sh >> logs/market_news.log 2>&1
```

### 2. 이메일 포맷 커스터마이징

HTML 템플릿: `core/utils/market_news_email_template.py`
- 색상 변경
- 레이아웃 조정
- 섹션 추가/제거

### 3. 뉴스 소스 확장

실제 API 연동:
```python
# core/agents/market_news_crew.py
# Mock 데이터를 실제 API로 교체
# - NewsAPI.org
# - Finnhub
# - Financial Times RSS
```

### 4. Slack 알림 추가

```python
from slack_sdk import WebClient

client = WebClient(token=os.getenv("SLACK_TOKEN"))
client.chat_postMessage(
    channel="market-news",
    text="📰 오늘의 시장 뉴스를 발송했습니다."
)
```

## 참고 자료

- [Python smtplib 문서](https://docs.python.org/3/library/smtplib.html)
- [Gmail SMTP 설정](https://support.google.com/mail/answer/7126229)
- [MIME 이메일 형식](https://docs.python.org/3/library/email.mime.html)
- [Crontab 가이드](https://crontab.guru)
