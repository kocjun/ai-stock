# 투자 성과 보고서 이메일 자동화 설정 가이드

## 개요

이 가이드는 Python 스크립트에서 생성한 HTML 형식의 투자 성과 보고서를 N8N을 통해 이메일로 자동 발송하는 방법을 설명합니다.

## 아키텍처

```
┌─────────────────────────────────┐
│ performance_reporter.py         │
│ (일일/주간 보고서 생성)           │
└──────────────┬──────────────────┘
               │ HTML 보고서 + 메타데이터
               │ (subject, recipient_email)
               ▼
┌─────────────────────────────────┐
│ N8N Webhook (report-webhook)    │
│ POST /webhook/report-webhook    │
└──────────────┬──────────────────┘
               │ JSON 페이로드
               ▼
┌─────────────────────────────────┐
│ N8N Workflow:                   │
│ report_webhook_workflow.json    │
│                                 │
│ 1. 웹훅 수신                    │
│ 2. 형식 확인 (HTML)            │
│ 3. 이메일 발송                  │
└──────────────┬──────────────────┘
               │
               ▼
        ┌──────────────┐
        │ 사용자 이메일함│
        └──────────────┘
```

## 필수 환경 변수 설정

### 1. N8N 웹훅 URL

```bash
# .env 파일에 추가
export N8N_WEBHOOK_URL="http://your-n8n-instance:5678/webhook/report-webhook"
```

또는 N8N이 로컬호스트에 설치된 경우:

```bash
export N8N_WEBHOOK_URL="http://localhost:5678/webhook/report-webhook"
```

### 2. 이메일 설정

```bash
# 발신자 이메일 주소
export EMAIL_FROM_ADDRESS="noreply@yourcompany.com"

# 보고서 수신자 이메일 주소 (기본값)
export REPORT_EMAIL_RECIPIENT="your-email@example.com"
```

### 3. N8N 이메일 크레덴셜 (N8N UI에서 설정)

N8N 대시보드에서 다음 단계를 수행합니다:

1. **Credentials 관리 접속**
   - N8N 대시보드 왼쪽 메뉴 → "Credentials"

2. **이메일 크레덴셜 생성**
   - "Create New" 버튼 클릭
   - "SMTP" 또는 "Gmail" 선택

3. **SMTP 설정 (Gmail 사용 예)**
   - **Host**: `smtp.gmail.com`
   - **Port**: `587`
   - **User**: `your-email@gmail.com`
   - **Password**: [Gmail 앱 비밀번호] (2단계 인증 활성화 필수)
   - **Use TLS**: 체크
   - **Connection URL**: (선택사항)

4. **다른 메일 서비스의 경우**
   - **Outlook/Microsoft 365**: `smtp.office365.com:587`
   - **AWS SES**: `email-smtp.region.amazonaws.com:587`
   - **회사 메일 서버**: IT 부서에 SMTP 정보 문의

## N8N 워크플로우 설정

### 워크플로우 파일 임포트

1. N8N 대시보드 접속
2. **메뉴 → Import from File** 클릭
3. `n8n_workflows/report_webhook_workflow.json` 파일 선택
4. 임포트 완료

### 워크플로우 구조

워크플로우는 다음 노드로 구성됩니다:

#### 1. **Webhook Trigger (보고서 웹훅 수신)**
   - **경로**: `report-webhook`
   - **메서드**: POST
   - **역할**: Python 스크립트로부터의 HTTP 요청 수신

#### 2. **Check Format (형식 확인)**
   - **조건**: `format == "html"`
   - **역할**: HTML 형식인지 확인하고 분기 처리

#### 3. **Send HTML Email (HTML 이메일 발송)**
   - **From**: `EMAIL_FROM_ADDRESS` 환경변수
   - **To**: 페이로드의 `recipient_email` 또는 `REPORT_EMAIL_RECIPIENT` 환경변수
   - **Subject**: 페이로드의 `subject`
   - **Body**: HTML 형식 (`content` 또는 `report` 필드)

#### 4. **Send Fallback Email (대체 이메일)**
   - **조건**: HTML 형식이 아닌 경우
   - **역할**: 마크다운이나 다른 형식을 텍스트로 발송

#### 5. **Webhook Response (응답)**
   - 성공 또는 실패 응답을 Python 스크립트로 반환

## Python 코드 사용 예

### 기본 사용법

```python
from paper_trading.performance_reporter import send_report_to_n8n

# HTML 보고서 생성 (자동)
html_report = format_html_report(report_data)

# N8N으로 전송
send_report_to_n8n(
    report_content=html_report,
    subject="일일 성과 보고서",
    recipient_email="trader@example.com"
)
```

### 함수 시그니처

```python
def send_report_to_n8n(
    report_content: str,
    webhook_url: Optional[str] = None,
    is_html: bool = True,
    subject: str = None,
    recipient_email: str = None
) -> bool:
    """
    Args:
        report_content: HTML 또는 마크다운 보고서 내용
        webhook_url: N8N 웹훅 URL (기본값: N8N_WEBHOOK_URL 환경변수)
        is_html: HTML 형식 여부 (기본값: True)
        subject: 이메일 제목 (기본값: '투자 성과 보고서')
        recipient_email: 수신자 이메일 (기본값: REPORT_EMAIL_RECIPIENT 환경변수)

    Returns:
        bool: 전송 성공 여부
    """
```

## 일일/주간 보고서 자동 발송 설정

### Cron 작업 예시

#### 일일 보고서 (매일 09:00)

```bash
# crontab -e
0 9 * * * cd /path/to/ai-agent && source .venv/bin/activate && python paper_trading/performance_reporter.py --account-id 1 --type daily --output /path/to/reports/daily_$(date +\%Y\%m\%d).md --save-db --send-n8n
```

#### 주간 보고서 (매주 토요일 09:00)

```bash
# crontab -e
0 9 * * 6 cd /path/to/ai-agent && source .venv/bin/activate && python paper_trading/performance_reporter.py --account-id 1 --type weekly --output /path/to/reports/weekly_$(date +\%Y\%m\%d).md --save-db --send-n8n
```

### 기존 Shell 스크립트 사용

프로젝트에 포함된 Shell 스크립트 사용:

```bash
# 일일 보고서
bash paper_trading/generate_daily_report.sh

# 주간 보고서
bash paper_trading/generate_weekly_report.sh
```

## 웹훅 페이로드 예시

Python 스크립트가 N8N으로 전송하는 JSON 페이로드:

```json
{
  "type": "performance_report",
  "timestamp": "2025-11-01T09:00:00.123456",
  "content": "<html>...</html>",
  "report": "<html>...</html>",
  "format": "html",
  "subject": "일일 성과 보고서",
  "recipient_email": "trader@example.com"
}
```

## 문제 해결

### 이메일이 안 오는 경우

#### 1. 환경 변수 확인

```bash
# N8N 웹훅 URL 확인
echo $N8N_WEBHOOK_URL

# 이메일 설정 확인
echo $EMAIL_FROM_ADDRESS
echo $REPORT_EMAIL_RECIPIENT

# 모든 설정 확인
env | grep -E "N8N_WEBHOOK|EMAIL_|REPORT_"
```

#### 2. N8N 워크플로우 활성화 확인

1. N8N 대시보드 접속
2. "report_webhook_workflow" 찾기
3. 상단 토글에서 "Active" 상태 확인
4. 비활성화된 경우 활성화 클릭

#### 3. 웹훅 경로 확인

```bash
# N8N 웹훅 목록 확인
# N8N 대시보드 → Webhooks 메뉴
# "report-webhook" 경로 존재 확인
```

#### 4. 이메일 크레덴셜 확인

1. N8N 대시보드 → Credentials
2. 이메일 크레덴셜 존재 확인
3. SMTP 설정이 올바른지 확인
4. 테스트 이메일 발송으로 연결 확인

```bash
# N8N 대시보드에서 Test Connection 클릭
```

#### 5. N8N 로그 확인

```bash
# N8N 컨테이너 로그 확인
docker logs n8n

# 또는 N8N UI의 Execution History 확인
# 대시보드 왼쪽 메뉴 → Executions
```

#### 6. Python 스크립트 테스트

```bash
# 테스트 발송
cd /path/to/ai-agent
source .venv/bin/activate

python paper_trading/performance_reporter.py \
  --account-id 1 \
  --type daily \
  --output /tmp/test_report.md \
  --save-db \
  --send-n8n
```

### 웹훅 응답 확인

Python 스크립트 실행 후 다음과 같은 메시지가 나타나야 합니다:

```
✅ n8n 전송 성공: 200
```

만약 다음이 나타나면:

```
⚠️  N8N_WEBHOOK_URL이 설정되지 않았습니다
```

→ 환경 변수를 다시 설정하세요.

### 이메일 형식 문제

HTML 이메일이 웹메일 클라이언트에서 제대로 표시되지 않는 경우:

1. **Gmail**: 스팸 폴더 확인
2. **Outlook**: 수신 거부 목록 확인
3. **기타**: 이메일 클라이언트의 "이미지 보기 허용" 설정 확인

## 모바일 친화적 HTML 이메일

현재 구현된 HTML 보고서는 다음 기능을 포함합니다:

- **반응형 CSS**: 모바일, 태블릿, 데스크톱 지원
- **CSS 그리드**: 자동 레이아웃 조정
- **미디어 쿼리**:
  - 768px 이하: 태블릿 레이아웃
  - 480px 이하: 모바일 레이아웃
- **인라인 스타일**: 이메일 클라이언트 호환성

테스트:

1. 실제 휴대폰으로 이메일 받기
2. 여러 이메일 클라이언트 (Gmail, Outlook, Apple Mail 등)에서 확인
3. 필요시 추가 CSS 조정

## 다음 단계

1. ✅ 환경 변수 설정
2. ✅ N8N 이메일 크레덴셜 설정
3. ✅ 워크플로우 임포트 및 활성화
4. ✅ 테스트 발송
5. ✅ Cron 작업 또는 N8N 스케줄 설정

## 참고 문서

- [N8N 공식 문서](https://docs.n8n.io/)
- [N8N Email Node](https://docs.n8n.io/nodes/n8n-nodes-base.emailSend/)
- [N8N Webhook](https://docs.n8n.io/nodes/n8n-nodes-base.webhook/)
- [Performance Reporter 사용법](./PAPER_TRADING_IMPLEMENTATION.md)
