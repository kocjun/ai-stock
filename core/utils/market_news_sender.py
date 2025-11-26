"""
시장 뉴스 이메일 발송 모듈

시장 뉴스 분석 결과를 SMTP 또는 N8N 웹훅을 통해 이메일로 발송
"""

import os
import sys
import json
import requests
import smtplib
from datetime import datetime
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional, List

# 프로젝트 루트 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# .env 파일 로드 (선택사항, 환경 변수로 override 가능)
try:
    from dotenv import load_dotenv
    env_file = project_root / ".env"
    if env_file.exists():
        load_dotenv(env_file)
except ImportError:
    pass  # python-dotenv 미설치 시 무시

from core.utils.market_news_email_template import create_market_news_payload, format_market_news_html


def send_market_news_via_smtp(
    report: str,
    recipient_email: Optional[str] = None,
    sender_email: Optional[str] = None,
    smtp_server: Optional[str] = None,
    smtp_port: Optional[int] = None,
    smtp_password: Optional[str] = None,
    news_items: Optional[List[Dict]] = None,
) -> bool:
    """
    SMTP를 이용한 직접 이메일 발송 (N8N 불필요)

    Args:
        report: AI가 생성한 뉴스 분석 리포트 (마크다운)
        recipient_email: 수신자 이메일 주소
        sender_email: 발송자 이메일 주소
        smtp_server: SMTP 서버 주소
        smtp_port: SMTP 서버 포트
        smtp_password: SMTP 비밀번호

    Returns:
        bool: 발송 성공 여부
    """

    # 환경 변수에서 설정 읽기
    if recipient_email is None:
        recipient_email = os.getenv("REPORT_EMAIL_RECIPIENT", os.getenv("EMAIL_TO"))

    if sender_email is None:
        sender_email = os.getenv("EMAIL_FROM", "noreply@investment.com")

    if smtp_server is None:
        smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")

    if smtp_port is None:
        smtp_port = int(os.getenv("SMTP_PORT", "587"))

    if smtp_password is None:
        smtp_password = os.getenv("SMTP_PASSWORD")

    if not recipient_email:
        print("❌ 수신자 이메일이 설정되지 않았습니다")
        return False

    if not smtp_password:
        print("❌ SMTP 비밀번호가 설정되지 않았습니다")
        return False

    try:
        print(f"📧 SMTP를 통한 이메일 발송 중...")
        print(f"   발송자: {sender_email}")
        print(f"   수신자: {recipient_email}")
        print(f"   SMTP 서버: {smtp_server}:{smtp_port}")

        # HTML 콘텐츠 생성
        html_content = format_market_news_html(report, news_items)

        # 이메일 메시지 구성
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "📰 오늘의 시장 뉴스 분석 - 증시 오픈 전"
        msg["From"] = sender_email
        msg["To"] = recipient_email

        # HTML 부분 추가
        html_part = MIMEText(html_content, "html", "utf-8")
        msg.attach(html_part)

        # SMTP 연결 및 발송
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, smtp_password)
            server.send_message(msg)

        print(f"✅ SMTP를 통한 이메일 발송 성공")
        print(f"   크기: {len(html_content)} bytes")

        return True

    except smtplib.SMTPAuthenticationError:
        print(f"❌ SMTP 인증 실패: 이메일 주소나 비밀번호를 확인하세요")
        return False

    except smtplib.SMTPException as e:
        print(f"❌ SMTP 오류: {e}")
        return False

    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")
        import traceback
        traceback.print_exc()
        return False


def send_market_news_email(
    report: str,
    webhook_url: Optional[str] = None,
    recipient_email: Optional[str] = None,
    use_smtp: bool = True,
    news_items: Optional[List[Dict]] = None,
) -> bool:
    """
    시장 뉴스를 SMTP 또는 N8N 웹훅으로 이메일 발송

    Args:
        report: AI가 생성한 뉴스 분석 리포트 (마크다운)
        webhook_url: N8N 웹훅 URL (옵션)
        recipient_email: 수신자 이메일 주소
        use_smtp: SMTP 우선 사용 여부 (기본값: True)

    Returns:
        bool: 발송 성공 여부
    """

    # SMTP 우선 시도
    if use_smtp:
        smtp_result = send_market_news_via_smtp(report, recipient_email, news_items=news_items)
        if smtp_result:
            return True
        print("⚠️  SMTP 발송 실패, N8N 웹훅 시도...")

    # N8N 웹훅 폴백
    if webhook_url is None:
        webhook_url = os.getenv("N8N_WEBHOOK_URL")

    if not webhook_url:
        print("⚠️  N8N_WEBHOOK_URL이 설정되지 않았습니다")
        return False

    if recipient_email is None:
        recipient_email = os.getenv("REPORT_EMAIL_RECIPIENT")

    try:
        # 페이로드 생성
        payload = create_market_news_payload(report, news_items)

        # 수신자 이메일 추가
        if recipient_email:
            payload["recipient_email"] = recipient_email

        print(f"📧 N8N 웹훅으로 이메일 발송 중...")
        print(f"   수신자: {recipient_email or 'N8N 기본값'}")
        print(f"   웹훅: {webhook_url}")

        # N8N 웹훅으로 발송
        response = requests.post(webhook_url, json=payload, timeout=30)
        response.raise_for_status()

        print(f"✅ N8N 웹훅 발송 성공: {response.status_code}")
        print(f"📊 페이로드 크기: {len(json.dumps(payload))} bytes")

        return True

    except requests.exceptions.ConnectionError as e:
        print(f"❌ N8N 연결 실패: {e}")
        print(f"   웹훅 URL이 올바른지 확인하세요: {webhook_url}")
        return False

    except requests.exceptions.Timeout:
        print(f"❌ N8N 요청 타임아웃")
        return False

    except requests.exceptions.RequestException as e:
        print(f"❌ N8N 발송 실패: {e}")
        return False

    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """
    메인 실행 함수
    """
    print("=" * 60)
    print("📧 시장 뉴스 이메일 발송")
    print("=" * 60)

    # 샘플 리포트 (실제로는 market_news_crew.py에서 받음)
    sample_report = """
## 📊 시장 요약
오늘 글로벌 시장은 Fed 금리 관련 뉴스와 반도체 섹터의 호재 소식으로 혼조를 보일 것으로 예상됩니다.

## 🌍 글로벌 시장 (나스닥)
### ⚠️ 높은 영향도
- **Fed 금리 인상 신호**: 달러 강세로 수출주 약세
- **S&P 500 신고가**: 미국 경제 강세 지속

## 🔧 반도체 뉴스
### ⚠️ 높은 영향도
- **Samsung 3nm 공정 시작**: 장기 긍정 신호
- **TSMC 파운드리 호황**: 글로벌 반도체 회복 신호

## 🇰🇷 국내 뉴스
### ⚠️ 높은 영향도
- **한은 금리 결정**: 내일 결정, 인상 확률 높음
- **원/달러 환율**: 수출주 호재

## 📈 종합 평가
**호재 > 악재** (긍정 신호 강화)
"""

    print("\n1️⃣  환경 변수 확인")
    print("-" * 60)

    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = os.getenv("SMTP_PORT")
    smtp_password = os.getenv("SMTP_PASSWORD")
    email_from = os.getenv("EMAIL_FROM", os.getenv("EMAIL_FROM_ADDRESS"))
    email_to = os.getenv("REPORT_EMAIL_RECIPIENT", os.getenv("EMAIL_TO"))
    n8n_webhook = os.getenv("N8N_WEBHOOK_URL")

    if smtp_server and smtp_password:
        print(f"✅ SMTP_SERVER: {smtp_server}:{smtp_port}")
        print(f"✅ SMTP_PASSWORD: {'*' * 6}...설정됨")
    else:
        print("⚠️  SMTP 설정: 미설정")

    if email_from:
        print(f"✅ EMAIL_FROM: {email_from}")
    else:
        print("⚠️  EMAIL_FROM: 미설정")

    if email_to:
        print(f"✅ REPORT_EMAIL_RECIPIENT: {email_to}")
    else:
        print("⚠️  REPORT_EMAIL_RECIPIENT: 미설정")

    if n8n_webhook:
        print(f"✅ N8N_WEBHOOK_URL: {n8n_webhook[:50]}...")
    else:
        print("⚠️  N8N_WEBHOOK_URL: 미설정 (폴백으로 사용됨)")

    print("\n2️⃣  이메일 발송")
    print("-" * 60)

    # SMTP 우선 사용, N8N은 폴백
    success = send_market_news_email(sample_report, n8n_webhook, email_to, use_smtp=True)

    print("\n" + "=" * 60)
    if success:
        print("✅ 이메일 발송 완료")
        print("=" * 60)
        return 0
    else:
        print("❌ 이메일 발송 실패")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
