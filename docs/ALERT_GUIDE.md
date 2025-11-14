# 📢 Alert Manager 사용 가이드

## 개요

Alert Manager는 한국 주식시장의 중요한 이벤트를 자동으로 감지하고 알림을 전송하는 시스템입니다.

### 주요 기능

1. **가격 급락/급등 알림** - 전일 대비 급격한 가격 변동 감지
2. **손절선/목표가 알림** - 포트폴리오 리스크 관리
3. **리밸런싱 알림** - 포트폴리오 비중 이탈 감지

---

## 🎯 알림 타입 상세

### 1️⃣ 가격 급락/급등 알림

**목적**: 시장의 급격한 변동을 조기 감지

**동작 방식**:
- 데이터베이스에서 최근 2일 가격 비교
- 설정한 임계값(기본 5%) 이상 변동 시 알림
- 변동폭에 따라 심각도 자동 분류

**예시**:
```
📈 LG화학(051910) 급등 감지: +8.65%
   이전가: 310,000원 → 현재가: 336,800원
   심각도: 높음
```

**설정 가능한 값**:
- `threshold`: 임계값 (%, 기본값: 5.0)
- `days`: 비교 기간 (일, 기본값: 1)

---

### 2️⃣ 손절선/목표가 알림

**목적**: 감정 배제한 체계적 매매 지원

**동작 방식**:
- 포트폴리오의 각 종목에 대해 진입가 대비 수익률 계산
- 손절선(-10%) 도달: 🚨 높은 우선순위 알림
- 목표가(+20%) 도달: 🎯 중간 우선순위 알림

**예시**:
```
🚨 손절선 도달: 카카오(035720)
   진입가: 60,000원
   현재가: 53,400원
   수익률: -11.00%
   보유량: 100주
   → 권장: 손절 검토
```

```
🎯 목표가 도달: 삼성전자(005930)
   진입가: 70,000원
   현재가: 97,900원
   수익률: +39.86%
   보유량: 10주
   → 권장: 익절 검토
```

**설정 가능한 값**:
- `stop_loss_pct`: 손절선 (%, 기본값: -10.0)
- `take_profit_pct`: 목표가 (%, 기본값: +20.0)
- `portfolio`: 포트폴리오 정보 (필수)

**포트폴리오 형식**:
```python
[
    {
        'code': '005930',        # 종목코드
        'entry_price': 70000,    # 진입가
        'quantity': 10           # 보유량
    },
    {
        'code': '000660',
        'entry_price': 130000,
        'quantity': 5
    }
]
```

---

### 3️⃣ 리밸런싱 알림

**목적**: 최적 포트폴리오 비중 유지

**동작 방식**:
- 현재 포트폴리오 비중 계산
- 목표 비중과 비교하여 오차 계산
- 허용 오차(기본 5%p) 초과 시 알림

**예시**:
```
🔄 리밸런싱 필요
포트폴리오 총액: 15,000,000원
조정 필요 종목: 2개

1. 삼성전자(005930)
   현재 비중: 45.00%
   목표 비중: 30.00%
   차이: 15.00%p
   권장: 매도

2. NAVER(035420)
   현재 비중: 10.00%
   목표 비중: 20.00%
   차이: 10.00%p
   권장: 매수
```

**설정 가능한 값**:
- `target_weights`: 목표 비중 (필수)
- `portfolio`: 현재 포트폴리오 (필수)
- `threshold`: 허용 오차 (기본값: 0.05 = 5%p)

**포트폴리오 형식**:
```python
# 목표 비중
target_weights = {
    '005930': 0.30,  # 삼성전자 30%
    '000660': 0.25,  # SK하이닉스 25%
    '035420': 0.20,  # NAVER 20%
    '035720': 0.15,  # 카카오 15%
    '051910': 0.10   # LG화학 10%
}

# 현재 포트폴리오
portfolio = [
    {
        'code': '005930',
        'quantity': 10,
        'value': 979000  # 현재 평가액
    },
    {
        'code': '000660',
        'quantity': 5,
        'value': 2327500
    }
]
```

---

## 🚀 사용 방법

### 방법 1: Python 스크립트 직접 실행

```bash
# 가상환경 활성화
source .venv/bin/activate

# Alert Manager 실행
python alert_manager.py
```

**출력 결과**:
```
============================================================
Alert Manager 테스트
============================================================

테스트 1: 가격 급락/급등 감지 (±5% 이상)
------------------------------------------------------------

✅ 4개 알림 발견

  LG화학(051910) 급등 감지: +8.65%
  삼성SDI(006400) 급등 감지: +8.26%
  한국전력(015760) 급등 감지: +6.22%
  고려아연(010130) 급락 감지: -5.19%

============================================================
테스트 2: 손절선/목표가 체크
------------------------------------------------------------

✅ 2개 알림 발견

  🎯 목표가 도달: 삼성전자(005930) +39.86% (목표: 20.0%)
  🎯 목표가 도달: SK하이닉스(000660) +258.08% (목표: 20.0%)

============================================================
```

---

### 방법 2: 커스텀 스크립트 작성

```python
# custom_alert.py
from alert_manager import (
    check_price_alerts,
    check_threshold_alerts,
    check_rebalance_alerts
)

# 1. 가격 알림 (10% 이상 변동)
price_alerts = check_price_alerts(threshold=10.0, days=1)
for alert in price_alerts:
    print(alert['message'])

# 2. 내 포트폴리오 손절선/목표가 체크
my_portfolio = [
    {'code': '005930', 'entry_price': 75000, 'quantity': 20},
    {'code': '000660', 'entry_price': 140000, 'quantity': 10},
]

threshold_alerts = check_threshold_alerts(
    portfolio=my_portfolio,
    stop_loss_pct=-8.0,   # 8% 손절선
    take_profit_pct=15.0  # 15% 목표가
)

for alert in threshold_alerts:
    print(alert['message'])

# 3. 리밸런싱 체크
target_weights = {
    '005930': 0.40,
    '000660': 0.30,
    '035420': 0.30
}

current_portfolio = [
    {'code': '005930', 'quantity': 20, 'value': 1958000},
    {'code': '000660', 'quantity': 10, 'value': 4655000},
    {'code': '035420', 'quantity': 15, 'value': 3832500}
]

rebalance_alerts = check_rebalance_alerts(
    portfolio=current_portfolio,
    target_weights=target_weights,
    threshold=0.03  # 3%p 허용 오차
)

if len(rebalance_alerts) > 0:
    for alert in rebalance_alerts:
        print(f"리밸런싱 필요: {len(alert['rebalance_list'])}개 종목")
```

---

### 방법 3: n8n 워크플로 자동화

#### 설정 단계

1. **n8n 접속**: http://localhost:5678
2. **워크플로 가져오기**:
   - Workflows → Import from File
   - `n8n_workflows/alert_workflow.json` 선택
3. **Slack/Email 설정**:
   - Slack Webhook URL 입력
   - 이메일 설정 (SMTP)
4. **스케줄 조정**:
   - 기본: 매일 오전 9시 30분
   - 원하는 시간으로 변경 가능
5. **활성화**: 우측 상단 "Active" 토글 ON

#### 알림 전송 채널

**Slack 알림**:
```
🔔 주식 시장 알림

📈 가격 급등/급락 (4건)
  • LG화학(051910) 급등 감지: +8.65%
  • 삼성SDI(006400) 급등 감지: +8.26%
  ...

🎯 손절선/목표가 도달 (2건)
  • 삼성전자(005930): +39.86%
  • SK하이닉스(000660): +258.08%
```

**이메일 알림**:
- 제목: 🔔 주식 시장 알림
- 본문: 알림 상세 내용
- 첨부: 없음

---

### 방법 4: cron job으로 자동 실행

```bash
# crontab 편집
crontab -e

# 추가: 매일 오전 9시 30분 실행
30 9 * * 1-5 cd /Users/yeongchang.jeon/workspace/ai-agent && source .venv/bin/activate && python alert_manager.py >> logs/alert_$(date +\%Y\%m\%d).log 2>&1

# 또는: 3시간마다 실행 (장 중 모니터링)
0 */3 * * 1-5 cd /Users/yeongchang.jeon/workspace/ai-agent && source .venv/bin/activate && python alert_manager.py >> logs/alert_$(date +\%Y\%m\%d).log 2>&1
```

---

## 📊 실제 사용 예시

### 시나리오 1: 급락 대응

**상황**:
```
📉 카카오(035720) 급락 감지: -7.5%
   이전가: 62,000원 → 현재가: 57,350원
   심각도: 높음
```

**대응**:
1. 뉴스 확인 (실적 악화? 시장 전체 하락?)
2. 기술적 지표 확인 (과매도 상태?)
3. 추가 매수 또는 관망 결정

---

### 시나리오 2: 손절선 도달

**상황**:
```
🚨 손절선 도달: LG화학(051910)
   진입가: 360,000원
   현재가: 318,000원
   수익률: -11.67%
   보유량: 5주
```

**대응**:
1. 포트폴리오 전체 점검
2. 손절 또는 추가 매수 판단
3. 감정 배제하고 원칙대로 실행

---

### 시나리오 3: 목표가 도달

**상황**:
```
🎯 목표가 도달: 삼성전자(005930)
   진입가: 70,000원
   현재가: 97,900원
   수익률: +39.86%
   보유량: 10주
```

**대응**:
1. 전량 익절 또는 부분 익절
2. 목표가 상향 조정 검토
3. 수익 재투자 계획 수립

---

### 시나리오 4: 리밸런싱

**상황**:
```
🔄 리밸런싱 필요
포트폴리오 총액: 15,000,000원

1. 삼성전자(005930)
   현재: 45% → 목표: 30% (15%p 초과)
   권장: 2,250,000원 매도

2. NAVER(035420)
   현재: 10% → 목표: 20% (10%p 부족)
   권장: 1,500,000원 매수
```

**대응**:
1. 시장 상황 확인 (타이밍 조정)
2. 거래 비용 고려
3. 리밸런싱 실행

---

## 🔧 고급 설정

### 알림 임계값 커스터마이징

```python
# alert_config.py
ALERT_CONFIG = {
    # 가격 알림
    'price': {
        'threshold': 7.0,    # 7% 이상만 알림
        'days': 1,
        'severity_high': 10.0  # 10% 이상은 높은 심각도
    },

    # 손절선/목표가
    'threshold': {
        'stop_loss': -8.0,    # 8% 손절
        'take_profit': 25.0,  # 25% 익절
        'trailing_stop': -5.0 # 추적 손절 (고급)
    },

    # 리밸런싱
    'rebalance': {
        'threshold': 0.03,    # 3%p 허용 오차
        'min_trade': 100000,  # 최소 거래금액
        'frequency': 'monthly'  # 리밸런싱 주기
    }
}
```

### 알림 필터링

```python
# 특정 종목만 모니터링
WATCH_LIST = ['005930', '000660', '035420', '035720', '051910']

# 가격 알림 - 관심 종목만
price_alerts = check_price_alerts(threshold=5.0)
filtered = [a for a in price_alerts if a['code'] in WATCH_LIST]

# 섹터별 필터링
IT_SECTOR = ['035420', '035720']  # NAVER, 카카오
CHEM_SECTOR = ['051910', '006400']  # LG화학, 삼성SDI

it_alerts = [a for a in price_alerts if a['code'] in IT_SECTOR]
```

### Webhook 연동

```python
from tools.n8n_webhook_tool import N8nWebhookTool

webhook = N8nWebhookTool(webhook_url=os.getenv("N8N_WEBHOOK_URL"))

# 알림 발생 시 n8n으로 전송
price_alerts = check_price_alerts(threshold=5.0)

if len(price_alerts) > 0:
    webhook.run({
        'type': 'price_alert',
        'count': len(price_alerts),
        'alerts': price_alerts[:5],  # 상위 5개만
        'timestamp': datetime.now().isoformat()
    })
```

---

## 📱 알림 채널 설정

### Slack 연동

1. **Webhook URL 생성**:
   - https://api.slack.com/messaging/webhooks
   - Incoming Webhooks 앱 설치
   - 채널 선택 및 URL 복사

2. **.env 파일 추가**:
```bash
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

3. **알림 전송 스크립트**:
```python
import requests
import json

def send_slack_alert(alerts):
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")

    message = "🔔 *주식 시장 알림*\n\n"
    for alert in alerts:
        message += f"• {alert['message']}\n"

    payload = {"text": message}

    response = requests.post(
        webhook_url,
        data=json.dumps(payload),
        headers={'Content-Type': 'application/json'}
    )

    return response.status_code == 200

# 사용
price_alerts = check_price_alerts(threshold=5.0)
if len(price_alerts) > 0:
    send_slack_alert(price_alerts)
```

### 이메일 연동

```python
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_email_alert(alerts):
    sender = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASSWORD")
    receiver = os.getenv("ALERT_EMAIL")

    msg = MIMEMultipart()
    msg['From'] = sender
    msg['To'] = receiver
    msg['Subject'] = "🔔 주식 시장 알림"

    body = "주식 시장 알림\n\n"
    for alert in alerts:
        body += f"• {alert['message']}\n"

    msg.attach(MIMEText(body, 'plain'))

    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(sender, password)
        server.send_message(msg)

# 사용
price_alerts = check_price_alerts(threshold=5.0)
if len(price_alerts) > 0:
    send_email_alert(price_alerts)
```

---

## 🐛 문제 해결

### 알림이 발생하지 않음

**원인**:
- 데이터베이스에 가격 데이터 부족
- 임계값이 너무 높게 설정됨
- 시장 변동성이 낮은 시기

**해결**:
```bash
# 데이터 확인
docker exec investment_postgres psql -U invest_user -d investment_db -c "
SELECT COUNT(*) as total_prices,
       MAX(date) as latest_date
FROM prices;
"

# 임계값 낮추기 (3%로 시도)
python -c "
from alert_manager import check_price_alerts
alerts = check_price_alerts(threshold=3.0)
print(f'{len(alerts)}개 알림')
"
```

### 너무 많은 알림

**해결**:
1. 임계값 상향 조정 (5% → 7%)
2. 알림 필터링 (관심 종목만)
3. 알림 빈도 조정 (1일 1회)

### 순환 import 오류

**현상**:
```
ImportError: cannot import name 'check_price_alerts' from partially initialized module 'alert_manager'
```

**해결**:
- `alert_manager.py`를 직접 실행 (정상 작동)
- 모듈 import 구조 개선 필요 (향후 리팩토링)

---

## 📈 성능 최적화

### 데이터베이스 인덱스

```sql
-- 알림 성능 향상을 위한 인덱스
CREATE INDEX IF NOT EXISTS idx_prices_date_desc
ON prices(code, date DESC);

CREATE INDEX IF NOT EXISTS idx_prices_code_close
ON prices(code, close);
```

### 캐싱

```python
from functools import lru_cache
from datetime import datetime, timedelta

@lru_cache(maxsize=128)
def get_cached_alerts(date_str: str, threshold: float):
    """당일 알림 캐싱"""
    return check_price_alerts(threshold=threshold)

# 사용
today = datetime.now().strftime('%Y-%m-%d')
alerts = get_cached_alerts(today, 5.0)
```

---

## 🎯 다음 단계

### 구현 예정 기능

1. **추적 손절 (Trailing Stop)**
   - 최고가 대비 N% 하락 시 알림
   - 상승장에서 수익 극대화

2. **기술적 지표 알림**
   - RSI 과매수/과매도 알림
   - 골든크로스/데드크로스 감지

3. **뉴스 감성 분석 알림**
   - 악재/호재 뉴스 자동 분류
   - 감성 점수 기반 알림

4. **웹 대시보드**
   - 실시간 알림 히스토리
   - 시각화 차트

---

## 📞 지원

문제가 발생하면:
1. 로그 확인: `logs/alert_*.log`
2. 데이터베이스 상태 확인
3. [CLAUDE.md](CLAUDE.md) 참조
4. [README.md](README.md) 참조

---

**최종 업데이트**: 2025-10-18
**버전**: 1.0
