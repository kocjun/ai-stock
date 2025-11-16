# .env 파일을 사용한 환경 변수 관리

## 개요

이제 시장 뉴스 시스템이 **`.env` 파일에서 자동으로 환경 변수를 로드**합니다. 더 이상 매번 환경 변수를 수동으로 설정할 필요가 없습니다.

## 지원되는 파일 로드 방식

### 1️⃣ Shell Script (`.env` 파일 로드)

`scripts/send_market_news.sh`는 실행 시 자동으로 `.env` 파일을 로드합니다:

```bash
#!/bin/bash

# .env 파일 로드 (주석과 빈 줄 제외)
if [ -f "${PROJECT_ROOT}/.env" ]; then
    set -a
    source <(grep -v '^#' "${PROJECT_ROOT}/.env" | grep -v '^$')
    set +a
fi
```

**장점:**
- 복잡한 값 (공백 포함 비밀번호 등) 정확하게 처리
- bash 4.1+ 지원

### 2️⃣ Python 코드 (python-dotenv 로드)

Python 모듈들은 `python-dotenv` 라이브러리를 사용합니다:

**core/agents/market_news_crew.py:**
```python
try:
    from dotenv import load_dotenv
    env_file = project_root / ".env"
    if env_file.exists():
        load_dotenv(env_file)
except ImportError:
    pass  # python-dotenv 미설치 시 무시
```

**core/utils/market_news_sender.py:**
```python
try:
    from dotenv import load_dotenv
    env_file = project_root / ".env"
    if env_file.exists():
        load_dotenv(env_file)
except ImportError:
    pass
```

**장점:**
- 표준 `.env` 형식 지원
- 환경 변수가 없으면 계속 실행 가능

## .env 파일 형식

### 올바른 형식

```bash
# 주석은 # 로 시작
KEY=value

# 공백이 있는 값은 따옴표로 감싸기
SMTP_PASSWORD="qhir ehsr izqx lmzx"

# 특수 문자가 있는 값
DB_PASSWORD="p@ss!word123"

# 빈 줄은 무시됨
ANOTHER_KEY=another_value
```

### 현재 .env 파일의 이메일 설정

```bash
# SMTP 서버 설정
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587

# 이메일 주소
EMAIL_FROM=kocjun@gmail.com
EMAIL_TO=kocjun@gmail.com

# Gmail 앱 비밀번호 (공백 포함, 따옴표 필수)
SMTP_PASSWORD="qhir ehsr izqx lmzx"
```

## 사용 방법

### 자동 로드 (권장)

이제 더 이상 환경 변수를 설정할 필요가 없습니다!

```bash
# 그냥 실행하면 .env 파일에서 자동으로 로드됨
bash scripts/send_market_news.sh
```

### 환경 변수로 Override (선택사항)

필요하면 환경 변수로 override 가능합니다:

```bash
# 특정 이메일로 발송
export EMAIL_TO="other-email@example.com"
bash scripts/send_market_news.sh

# 다른 SMTP 서버 사용
export SMTP_SERVER="smtp.sendgrid.net"
export SMTP_PASSWORD="SendGrid_API_Key"
bash scripts/send_market_news.sh
```

**우선순위:**
1. **환경 변수** (export로 설정한 값) - 최우선
2. **.env 파일** (default)
3. **코드의 기본값** (있으면)

## 테스트 결과

### 최신 테스트 (2025-11-05 20:44:30)

```
[20:44:25] ✅ .env 파일 발견, 환경 변수 로드
[20:44:25] ✅ SMTP_SERVER 설정됨: smtp.gmail.com
[20:44:25] ✅ 발송자 이메일 설정됨
[20:44:25] ✅ 수신자 이메일 설정됨
[20:44:25] ✅ SMTP_PASSWORD 설정됨
[20:44:30] ✅ 뉴스 분석 및 이메일 발송 완료

📧 SMTP를 통한 이메일 발송 중...
   발송자: kocjun@gmail.com
   수신자: kocjun@gmail.com
   SMTP 서버: smtp.gmail.com:587
✅ SMTP를 통한 이메일 발송 성공
   크기: 14775 bytes
```

## 보안 주의사항

### ✅ 안전한 방법
- ✅ `.env` 파일에 민감한 정보 저장
- ✅ `.gitignore`에 `.env` 추가되어 있음 (Git에 commit 안됨)
- ✅ 공개 저장소에 `.env.example` 파일 제공 (값 없음)

### ❌ 피해야 할 것
- ❌ 비밀번호를 코드에 하드코딩하기
- ❌ `.env` 파일을 Git에 commit하기
- ❌ 환경 변수를 로그에 기록하기

## FAQ

### Q1: .env 파일을 수정하면 자동으로 반영되나요?

**A:** 네, 완전히 반영됩니다. 스크립트 실행 시마다 `.env` 파일을 새로 읽습니다.

### Q2: .env 파일이 없으면 어떻게 되나요?

**A:**
- **Shell script**: 경고만 표시하고 계속 실행 (환경 변수가 없으면 SMTP 발송 실패)
- **Python**: 무시하고 계속 실행 (환경 변수가 없으면 기본값 사용)

### Q3: 비밀번호에 특수 문자가 있으면?

**A:** 따옴표로 감싸면 됩니다:

```bash
# 올바른 방법
SMTP_PASSWORD="p@ss!word"
DB_PASSWORD="user:pass@host"

# 잘못된 방법 (작동 안됨)
SMTP_PASSWORD=p@ss!word
```

### Q4: .env 파일의 우선순위는?

**A:** 환경 변수 > .env 파일 > 코드의 기본값

```bash
# 이 경우 email2@example.com으로 발송됨
export EMAIL_TO="email2@example.com"  # 이것 사용
bash scripts/send_market_news.sh       # .env의 email1@example.com은 무시됨
```

### Q5: 여러 .env 파일을 사용할 수 있나요?

**A:** 현재는 프로젝트 루트의 `.env` 파일만 지원합니다. 필요하면:

```bash
# 방법 1: 환경 변수로 override
export EMAIL_TO="custom@example.com"

# 방법 2: 다른 .env 파일의 내용을 임시 환경 변수로 로드
source /path/to/other/.env
```

## 다음 단계

### 1. Crontab 설정 (자동 실행)

```bash
crontab -e

# 평일 오전 7시에 자동 실행
0 7 * * 1-5 \
    cd /Users/yeongchang.jeon/workspace/ai-agent && \
    bash scripts/send_market_news.sh >> logs/market_news.log 2>&1
```

### 2. 예약된 실행 확인

```bash
# Crontab 목록 확인
crontab -l

# 로그 확인
tail -50 logs/market_news_*.log
```

### 3. 다른 환경 변수 추가 (필요시)

`.env` 파일에 추가:
```bash
# Slack 알림 (선택)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...

# 데이터베이스 (선택)
DB_HOST=localhost
DB_USER=invest_user
DB_PASSWORD="db_password_123"
```

## 참고 문서

- 기본 설정: `docs/MARKET_NEWS_SETUP.md`
- SMTP 상세: `docs/MARKET_NEWS_SMTP_FIX.md`
- 시스템 개요: `docs/MARKET_NEWS_SYSTEM_SUMMARY.md`
