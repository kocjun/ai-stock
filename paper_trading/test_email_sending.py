#!/usr/bin/env python3
"""
이메일 발송 테스트 스크립트

이 스크립트는 N8N 웹훅과 이메일 설정이 올바르게 작동하는지 테스트합니다.
"""

import os
import sys
import argparse
import requests
from datetime import datetime
from pathlib import Path

# 프로젝트 루트 디렉토리 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def create_test_html_report():
    """테스트용 HTML 보고서 생성"""
    html = """
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>투자 성과 보고서 - 테스트</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f5f5f5;
            }
            .container {
                background-color: white;
                border-radius: 8px;
                padding: 30px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }
            h1 {
                color: #2c3e50;
                border-bottom: 3px solid #3498db;
                padding-bottom: 10px;
                margin-bottom: 20px;
            }
            .header {
                display: flex;
                justify-content: space-between;
                margin-bottom: 30px;
                flex-wrap: wrap;
            }
            .date {
                color: #7f8c8d;
                font-size: 14px;
            }
            .status {
                background-color: #d4edda;
                color: #155724;
                padding: 8px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
            .section {
                margin-bottom: 30px;
            }
            .section-title {
                font-size: 18px;
                font-weight: bold;
                color: #2c3e50;
                margin-bottom: 15px;
                padding-bottom: 8px;
                border-bottom: 2px solid #ecf0f1;
            }
            .stats {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
                gap: 15px;
                margin-bottom: 15px;
            }
            .stat-box {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                border-radius: 8px;
                text-align: center;
            }
            .stat-label {
                font-size: 12px;
                opacity: 0.9;
                margin-bottom: 5px;
            }
            .stat-value {
                font-size: 24px;
                font-weight: bold;
            }
            .positive {
                background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
            }
            .negative {
                background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%);
            }
            .info-box {
                background-color: #e7f3ff;
                border-left: 4px solid #2196F3;
                padding: 15px;
                margin: 15px 0;
                border-radius: 4px;
            }
            .info-box strong {
                color: #1565c0;
            }
            @media (max-width: 768px) {
                .container {
                    padding: 15px;
                }
                .stats {
                    grid-template-columns: repeat(2, 1fr);
                }
                .header {
                    flex-direction: column;
                }
            }
            @media (max-width: 480px) {
                .container {
                    padding: 10px;
                }
                .stats {
                    grid-template-columns: 1fr;
                }
                h1 {
                    font-size: 18px;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div>
                    <h1>📊 투자 성과 보고서</h1>
                    <p class="date">테스트 이메일 - """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """</p>
                </div>
                <div class="status">✅ 테스트 완료</div>
            </div>

            <div class="info-box">
                <strong>📌 이 메일은 테스트입니다.</strong><br>
                N8N 웹훅이 올바르게 작동하고 있으며, 이메일 발송도 정상입니다.
            </div>

            <div class="section">
                <div class="section-title">📈 주요 지표</div>
                <div class="stats">
                    <div class="stat-box">
                        <div class="stat-label">총 수익률</div>
                        <div class="stat-value">+12.5%</div>
                    </div>
                    <div class="stat-box positive">
                        <div class="stat-label">실현 손익</div>
                        <div class="stat-value">+$1,250</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-label">Sharpe Ratio</div>
                        <div class="stat-value">1.45</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-label">Max Drawdown</div>
                        <div class="stat-value">-5.2%</div>
                    </div>
                </div>
            </div>

            <div class="section">
                <div class="section-title">✅ 시스템 상태</div>
                <ul>
                    <li>✅ Python 스크립트: 정상</li>
                    <li>✅ N8N 웹훅: 정상</li>
                    <li>✅ 이메일 발송: 정상</li>
                    <li>✅ HTML 렌더링: 정상</li>
                </ul>
            </div>

            <div class="section">
                <div class="section-title">🔧 다음 단계</div>
                <ol>
                    <li>이 이메일을 받았으면 모든 설정이 완료된 것입니다.</li>
                    <li>자동화된 일일/주간 보고서가 예약된 시간에 발송됩니다.</li>
                    <li>더 이상의 설정이 필요하지 않습니다.</li>
                </ol>
            </div>

            <hr style="margin: 30px 0; border: none; border-top: 1px solid #ecf0f1;">

            <p style="color: #7f8c8d; font-size: 12px;">
                이 이메일은 자동 발송되었습니다. 회신하지 마세요.
            </p>
        </div>
    </body>
    </html>
    """
    return html.strip()


def test_webhook_connection(webhook_url, recipient_email=None):
    """N8N 웹훅 연결 테스트"""
    print("\n" + "="*60)
    print("N8N 웹훅 연결 테스트")
    print("="*60)

    if not webhook_url:
        print("❌ N8N_WEBHOOK_URL이 설정되지 않았습니다.")
        return False

    print(f"🔗 웹훅 URL: {webhook_url}")

    try:
        payload = {
            "type": "test_report",
            "timestamp": datetime.now().isoformat(),
            "content": create_test_html_report(),
            "report": create_test_html_report(),
            "format": "html",
            "subject": "✅ 투자 성과 보고서 - 테스트 이메일",
            "recipient_email": recipient_email or os.getenv("REPORT_EMAIL_RECIPIENT")
        }

        print(f"📨 페이로드 크기: {len(str(payload))} bytes")
        print(f"📧 수신자: {payload['recipient_email']}")

        response = requests.post(webhook_url, json=payload, timeout=10)

        print(f"✅ 웹훅 요청 성공")
        print(f"📊 응답 코드: {response.status_code}")
        print(f"📝 응답 내용: {response.text[:200] if response.text else '(빈 응답)'}")

        return response.status_code == 200

    except Exception as e:
        print(f"❌ 웹훅 요청 실패: {e}")
        return False


def test_environment():
    """환경 변수 테스트"""
    print("\n" + "="*60)
    print("환경 변수 확인")
    print("="*60)

    env_vars = {
        "N8N_WEBHOOK_URL": "N8N 웹훅 URL",
        "EMAIL_FROM_ADDRESS": "발신 이메일 주소",
        "REPORT_EMAIL_RECIPIENT": "수신자 이메일 주소 (기본값)",
        "OPENAI_API_KEY": "OpenAI API 키 (선택)",
    }

    all_set = True
    for var, description in env_vars.items():
        value = os.getenv(var)
        if value:
            # 민감한 정보는 일부만 표시
            if var in ["OPENAI_API_KEY", "N8N_WEBHOOK_URL"]:
                display_value = f"{value[:20]}...{value[-10:]}" if len(value) > 30 else value
            else:
                display_value = value
            print(f"✅ {var}: {display_value}")
        else:
            print(f"⚠️  {var}: (미설정)")
            if var in ["N8N_WEBHOOK_URL", "EMAIL_FROM_ADDRESS", "REPORT_EMAIL_RECIPIENT"]:
                all_set = False

    return all_set


def main():
    parser = argparse.ArgumentParser(
        description="이메일 발송 시스템 테스트"
    )
    parser.add_argument(
        "--recipient",
        "-r",
        help="수신자 이메일 주소 (기본값: REPORT_EMAIL_RECIPIENT 환경변수)"
    )
    parser.add_argument(
        "--webhook",
        "-w",
        help="N8N 웹훅 URL (기본값: N8N_WEBHOOK_URL 환경변수)"
    )
    args = parser.parse_args()

    webhook_url = args.webhook or os.getenv("N8N_WEBHOOK_URL")
    recipient_email = args.recipient or os.getenv("REPORT_EMAIL_RECIPIENT")

    print("\n" + "="*60)
    print("📧 이메일 발송 시스템 테스트")
    print("="*60)

    # 1. 환경 변수 확인
    env_ok = test_environment()

    if not env_ok:
        print("\n❌ 필수 환경 변수가 설정되지 않았습니다.")
        print("\n설정 방법:")
        print("  export N8N_WEBHOOK_URL='http://your-n8n:5678/webhook/report-webhook'")
        print("  export EMAIL_FROM_ADDRESS='noreply@yourcompany.com'")
        print("  export REPORT_EMAIL_RECIPIENT='your-email@example.com'")
        sys.exit(1)

    # 2. 웹훅 연결 테스트
    webhook_ok = test_webhook_connection(webhook_url, recipient_email)

    # 결과 출력
    print("\n" + "="*60)
    print("📋 테스트 결과")
    print("="*60)

    if webhook_ok:
        print("✅ 모든 테스트가 성공했습니다!")
        print("\n✉️  이메일을 잠시만 기다려주세요...")
        print("   (일반적으로 1-5분 소요)")
        sys.exit(0)
    else:
        print("❌ 일부 테스트가 실패했습니다.")
        print("\n🔧 확인 사항:")
        print("  1. N8N 서버가 실행 중인지 확인")
        print("  2. 웹훅 URL이 정확한지 확인")
        print("  3. N8N 대시보드에서 웹훅 활성화 확인")
        print("  4. N8N 로그 확인: docker logs n8n")
        sys.exit(1)


if __name__ == "__main__":
    main()
