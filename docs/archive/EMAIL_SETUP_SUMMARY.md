# 이메일 자동 발송 설정 완료 요약

## 문제점 분석

사용자가 보고한 문제: **이메일이 도착하지 않음**

### 근본 원인
1. **Python 코드는 정상 작동**: HTML 형식으로 N8N 웹훅에 성공적으로 POST
2. **N8N 웹훅은 수신 중**: HTTP 200 응답 확인됨
3. **문제**: N8N에 이메일을 보낼 수 있는 워크플로우가 없었음

## 해결 방법

### 1️⃣ 새로운 N8N 워크플로우 생성 ✅
파일: `n8n_workflows/report_webhook_workflow.json`

**기능:**
- 웹훅 수신 (`/webhook/report-webhook`)
- HTML 형식 확인
- 이메일 발송 (N8N Email 노드 사용)
- 성공/실패 응답

### 2️⃣ Python 코드 개선 ✅
파일: `paper_trading/performance_reporter.py`

**개선사항:**
- `send_report_to_n8n()` 함수에 메타데이터 추가
  - `subject`: 이메일 제목
  - `recipient_email`: 수신자 이메일
- 호출 부분 업데이트 (동적 제목 설정)
- 페이로드 구조 확장 (호환성 유지)

### 3️⃣ 테스트 도구 제작 ✅
파일: `paper_trading/test_email_sending.py`

**기능:**
- 환경 변수 확인
- N8N 웹훅 연결 테스트
- HTML 이메일 발송 테스트

### 4️⃣ 상세 문서 작성 ✅
파일: `docs/EMAIL_WORKFLOW_SETUP.md`

**포함 사항:**
- 아키텍처 설명
- 환경 변수 설정 방법
- N8N 워크플로우 설정 단계
- Cron 작업 설정
- 문제 해결 가이드

## 🚀 빠른 시작

### 1단계: 환경 변수 설정

```bash
# .env 파일 또는 시스템 환경 변수로 설정
export N8N_WEBHOOK_URL="http://localhost:5678/webhook/report-webhook"
export EMAIL_FROM_ADDRESS="noreply@yourcompany.com"
export REPORT_EMAIL_RECIPIENT="your-email@example.com"
```

### 2단계: N8N 워크플로우 임포트

1. N8N 대시보드 접속
2. **Menu → Import from File**
3. `n8n_workflows/report_webhook_workflow.json` 선택
4. 활성화 버튼 클릭

### 3단계: N8N 이메일 크레덴셜 설정

N8N 대시보드에서:
1. **Credentials → Create New**
2. **SMTP** 선택 (Gmail, Outlook 등)
3. 메일 서버 정보 입력:
   - **Host**: `smtp.gmail.com` (Gmail의 경우)
   - **Port**: `587`
   - **User**: `your-email@gmail.com`
   - **Password**: [앱 비밀번호]

⚠️ **Gmail 사용 시 주의:**
- 2단계 인증 반드시 활성화
- [Google 앱 비밀번호](https://myaccount.google.com/apppasswords) 생성

### 4단계: 테스트 이메일 발송

```bash
cd /path/to/ai-agent
source .venv/bin/activate

# 테스트 스크립트 실행
python paper_trading/test_email_sending.py

# 또는 수신자 지정
python paper_trading/test_email_sending.py --recipient test@example.com
```

**예상 결과:**
```
✅ 환경 변수: 모두 설정됨
✅ 웹훅 요청 성공
📧 응답 코드: 200
```

## 📊 변경 사항 상세

### 수정된 파일

#### `paper_trading/performance_reporter.py`
```python
# 함수 시그니처 확장
def send_report_to_n8n(
    report_content: str,
    webhook_url: Optional[str] = None,
    is_html: bool = True,
    subject: str = None,           # NEW
    recipient_email: str = None     # NEW
) -> bool:

# 페이로드 구조 확장
payload = {
    "type": "performance_report",
    "timestamp": "...",
    "content": report_content,
    "report": report_content,      # 호환성
    "format": "html",
    "subject": subject,            # NEW
    "recipient_email": recipient_email  # NEW
}

# 호출 부분 업데이트
send_report_to_n8n(
    html_report,
    subject="일일/주간 성과 보고서",
    recipient_email=os.getenv("REPORT_EMAIL_RECIPIENT")
)
```

### 신규 파일

#### `n8n_workflows/report_webhook_workflow.json`
- 5개 노드로 구성
- 웹훅 → 형식 확인 → 이메일 발송 → 응답

#### `paper_trading/test_email_sending.py`
- 환경 확인 기능
- 웹훅 연결 테스트
- 테스트 이메일 발송
- 결과 보고

#### `docs/EMAIL_WORKFLOW_SETUP.md`
- 전체 아키텍처 설명
- 단계별 설정 가이드
- 문제 해결 팁

## 📱 모바일 최적화

HTML 이메일은 다음을 지원합니다:

✅ **응답형 CSS**
- 모바일 (480px 이하)
- 태블릿 (768px 이하)
- 데스크톱 (1024px 이상)

✅ **CSS 그리드**
```css
.stats {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
}

@media (max-width: 768px) {
    .stats { grid-template-columns: repeat(2, 1fr); }
}

@media (max-width: 480px) {
    .stats { grid-template-columns: 1fr; }
}
```

## ✅ 검증 체크리스트

다음을 확인하세요:

- [ ] 환경 변수 설정 (`N8N_WEBHOOK_URL`, `EMAIL_FROM_ADDRESS`, `REPORT_EMAIL_RECIPIENT`)
- [ ] N8N 서버 실행 중 확인
- [ ] N8N 워크플로우 임포트 완료
- [ ] 이메일 크레덴셜 설정 완료
- [ ] 테스트 이메일 수신 확인
- [ ] 모바일에서 이메일 확인 (형식 검증)

## 🔄 자동화 설정

### 일일 보고서 (매일 09:00)
```bash
# crontab -e
0 9 * * * cd /path/to/ai-agent && source .venv/bin/activate && \
  python paper_trading/performance_reporter.py \
  --account-id 1 --type daily --output ~/reports/daily_$(date +\%Y\%m\%d).md \
  --save-db --send-n8n
```

### 주간 보고서 (매주 토요일 09:00)
```bash
0 9 * * 6 cd /path/to/ai-agent && source .venv/bin/activate && \
  python paper_trading/performance_reporter.py \
  --account-id 1 --type weekly --output ~/reports/weekly_$(date +\%Y\%m\%d).md \
  --save-db --send-n8n
```

## 📞 문제 해결

### "이메일이 안 왔어요"
1. 테스트 스크립트 실행: `python paper_trading/test_email_sending.py`
2. 스팸 폴더 확인
3. N8N 로그 확인: `docker logs n8n | tail -50`
4. [이메일 설정 가이드](./docs/EMAIL_WORKFLOW_SETUP.md#문제-해결) 참조

### "웹훅이 작동하지 않아요"
1. N8N 웹훅이 활성화되었는지 확인
2. 경로가 `report-webhook`인지 확인
3. 웹훅 URL에 끝에 슬래시 없음 확인
4. `curl -X POST http://localhost:5678/webhook/report-webhook -H "Content-Type: application/json" -d '{}'` 테스트

### "N8N 연결 거부"
```bash
# N8N 컨테이너 확인
docker ps | grep n8n

# 포트 확인
netstat -tuln | grep 5678

# N8N 로그
docker logs n8n
```

## 다음 단계

1. ✅ **지금**: 환경 변수 설정 및 테스트 실행
2. ✅ **다음**: N8N 워크플로우 임포트 및 활성화
3. ✅ **최종**: Cron 작업으로 자동화

모든 단계가 완료되면 더 이상의 수작업이 필요 없습니다! 🎉

## 참고

- **이메일 설정 상세 가이드**: [docs/EMAIL_WORKFLOW_SETUP.md](./docs/EMAIL_WORKFLOW_SETUP.md)
- **Performance Reporter**: [paper_trading/README.md](./paper_trading/README.md)
- **N8N 공식 문서**: https://docs.n8n.io/
