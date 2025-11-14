"""
시장 뉴스 이메일 템플릿

오전 9시 증시 오픈 전 투자자들에게 발송할 HTML 이메일 템플릿
"""

from datetime import datetime
from typing import Dict, List, Any


def format_market_news_html(report_content: str, news_items: List[Dict] = None) -> str:
    """
    시장 뉴스를 HTML 이메일 형식으로 변환

    Args:
        report_content: AI가 생성한 뉴스 분석 리포트 (마크다운)
        news_items: 뉴스 아이템 리스트 (선택)

    Returns:
        HTML 형식의 이메일 콘텐츠
    """

    current_date = datetime.now().strftime("%Y년 %m월 %d일")
    day_of_week = ["월", "화", "수", "목", "금", "토", "일"][datetime.now().weekday()]

    html = f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>오늘의 시장 뉴스</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                font-family: 'Malgun Gothic', 'Apple SD Gothic Neo', Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                background: #f5f7fa;
                margin: 0;
                padding: 0;
            }}
            .container {{
                max-width: 900px;
                margin: 0 auto;
                padding: 15px;
            }}

            /* 헤더 */
            .header {{
                background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
                color: white;
                padding: 30px 20px;
                border-radius: 12px;
                margin-bottom: 20px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }}
            .header h1 {{
                margin: 0 0 10px 0;
                font-size: 28px;
                font-weight: 700;
            }}
            .header-meta {{
                display: flex;
                justify-content: space-between;
                margin-top: 15px;
                padding-top: 15px;
                border-top: 1px solid rgba(255,255,255,0.2);
                font-size: 13px;
                opacity: 0.9;
            }}
            .header-date {{
                font-weight: 600;
            }}
            .header-note {{
                text-align: right;
            }}

            /* 요약 섹션 */
            .summary {{
                background: white;
                padding: 20px;
                margin-bottom: 15px;
                border-radius: 10px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.08);
                border-left: 4px solid #ff6b6b;
            }}
            .summary h2 {{
                color: #ff6b6b;
                margin: 0 0 10px 0;
                font-size: 16px;
                text-transform: uppercase;
                letter-spacing: 1px;
            }}
            .summary-content {{
                font-size: 15px;
                line-height: 1.8;
                color: #555;
            }}

            /* 뉴스 섹션 */
            .news-section {{
                background: white;
                padding: 20px;
                margin-bottom: 15px;
                border-radius: 10px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            }}
            .news-section h2 {{
                color: white;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 12px 15px;
                margin: -20px -20px 15px -20px;
                border-radius: 10px 10px 0 0;
                font-size: 18px;
                font-weight: 600;
            }}

            /* 개별 뉴스 아이템 */
            .news-item {{
                padding: 15px;
                margin-bottom: 12px;
                background: #f9fafb;
                border-left: 4px solid #667eea;
                border-radius: 4px;
            }}
            .news-item.high-impact {{
                border-left-color: #ff6b6b;
                background: #fff5f5;
            }}
            .news-item.medium-impact {{
                border-left-color: #ffa500;
                background: #fffaf0;
            }}
            .news-item.low-impact {{
                border-left-color: #51cf66;
                background: #f0fdf4;
            }}

            .news-title {{
                font-weight: 600;
                font-size: 14px;
                color: #333;
                margin-bottom: 5px;
            }}
            .impact-badge {{
                display: inline-block;
                padding: 2px 8px;
                border-radius: 3px;
                font-size: 11px;
                font-weight: 600;
                margin-bottom: 8px;
            }}
            .impact-badge.high {{
                background: #ff6b6b;
                color: white;
            }}
            .impact-badge.medium {{
                background: #ffa500;
                color: white;
            }}
            .impact-badge.low {{
                background: #51cf66;
                color: white;
            }}

            .news-description {{
                font-size: 13px;
                color: #555;
                line-height: 1.6;
                margin-bottom: 8px;
            }}
            .news-source {{
                font-size: 12px;
                color: #999;
            }}

            /* 영향 받을 종목 */
            .affected-stocks {{
                margin-top: 10px;
                padding-top: 10px;
                border-top: 1px solid #e1e8ed;
            }}
            .affected-stocks-label {{
                font-size: 11px;
                color: #666;
                font-weight: 600;
                text-transform: uppercase;
                margin-bottom: 5px;
            }}
            .stock-tag {{
                display: inline-block;
                background: #667eea;
                color: white;
                padding: 3px 8px;
                border-radius: 3px;
                font-size: 11px;
                margin-right: 5px;
                margin-bottom: 5px;
            }}

            /* 추천 액션 */
            .recommendation {{
                background: #e7f5ff;
                border-left: 4px solid #339af0;
                padding: 10px;
                margin-top: 10px;
                border-radius: 4px;
                font-size: 12px;
                color: #1c7ed6;
            }}

            /* 종합 평가 */
            .overall-assessment {{
                background: white;
                padding: 20px;
                margin-bottom: 15px;
                border-radius: 10px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.08);
                border-top: 3px solid #1e3c72;
            }}
            .overall-assessment h2 {{
                color: #1e3c72;
                margin: 0 0 15px 0;
                font-size: 16px;
                text-transform: uppercase;
                letter-spacing: 1px;
            }}

            .assessment-item {{
                display: flex;
                align-items: center;
                margin-bottom: 12px;
                padding: 10px;
                background: #f9fafb;
                border-radius: 4px;
            }}
            .assessment-icon {{
                font-size: 24px;
                margin-right: 12px;
                min-width: 30px;
            }}
            .assessment-content {{
                flex: 1;
            }}
            .assessment-label {{
                font-weight: 600;
                color: #333;
                margin-bottom: 3px;
            }}
            .assessment-description {{
                font-size: 13px;
                color: #555;
            }}

            /* 주의사항 */
            .disclaimer {{
                background: #fff3cd;
                border-left: 4px solid #ffc107;
                padding: 15px;
                margin-bottom: 15px;
                border-radius: 4px;
                font-size: 12px;
                color: #856404;
            }}

            /* 푸터 */
            .footer {{
                text-align: center;
                color: #999;
                font-size: 11px;
                margin-top: 30px;
                padding-top: 20px;
                border-top: 2px solid #e1e8ed;
            }}
            .footer p {{
                margin: 4px 0;
            }}

            /* 모바일 반응형 */
            @media (max-width: 768px) {{
                .container {{ padding: 10px; }}
                .header {{ padding: 20px 15px; margin-bottom: 15px; }}
                .header h1 {{ font-size: 24px; margin-bottom: 8px; }}
                .header-meta {{ font-size: 12px; }}
                .news-section h2 {{ font-size: 16px; }}
                .news-item {{ padding: 12px; }}
                .impact-badge {{ font-size: 10px; padding: 2px 6px; }}
            }}

            @media (max-width: 480px) {{
                .container {{ padding: 8px; }}
                .header {{ padding: 15px 12px; margin-bottom: 12px; }}
                .header h1 {{ font-size: 20px; margin-bottom: 6px; }}
                .header-meta {{ flex-direction: column; }}
                .header-date {{ margin-bottom: 5px; }}
                .news-section h2 {{ font-size: 14px; }}
                .news-item {{ padding: 10px; }}
                .news-title {{ font-size: 13px; }}
                .news-description {{ font-size: 12px; }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <!-- 헤더 -->
            <div class="header">
                <h1>📰 오늘의 시장 뉴스</h1>
                <div class="header-meta">
                    <div class="header-date">{current_date} ({day_of_week}요일)</div>
                    <div class="header-note">증시 오픈 30분 전 분석</div>
                </div>
            </div>

            <!-- 뉴스 콘텐츠 -->
            <div style="background: white; padding: 20px; margin-bottom: 15px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
                <h2 style="color: #333; margin: 0 0 15px 0; font-size: 16px; border-bottom: 2px solid #667eea; padding-bottom: 10px;">📋 분석 리포트</h2>
                <div style="font-size: 14px; line-height: 1.8; color: #555;">
                    {format_report_content(report_content)}
                </div>
            </div>

            <!-- 주의사항 -->
            <div class="disclaimer">
                ⚠️ <strong>주의:</strong> 본 뉴스 분석은 정보 제공 목적입니다.
                투자 판단은 본인의 투자 철학과 리스크 관리 계획에 따라 직접 결정하세요.
            </div>

            <!-- 푸터 -->
            <div class="footer">
                <p>이 이메일은 자동으로 생성되었습니다.</p>
                <p>© 2025 투자 AI 에이전트 | 매일 오전 9시 발송</p>
            </div>
        </div>
    </body>
    </html>
    """

    return html.strip()


def format_report_content(content: str) -> str:
    """
    마크다운 형식의 리포트를 HTML로 변환하는 간단한 포매터
    """
    import re

    # 제목 변환
    content = re.sub(r'^## (.*?)$', r'<h3 style="color: #667eea; margin: 15px 0 10px 0; font-size: 16px; border-bottom: 2px solid #667eea; padding-bottom: 8px;">\1</h3>', content, flags=re.MULTILINE)
    content = re.sub(r'^### (.*?)$', r'<h4 style="color: #333; margin: 12px 0 8px 0; font-size: 14px;">\1</h4>', content, flags=re.MULTILINE)

    # 굵은 텍스트
    content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', content)
    content = re.sub(r'\*(.*?)\*', r'<em>\1</em>', content)

    # 리스트 변환
    content = re.sub(r'^\- (.*?)$', r'<li style="margin-left: 20px; margin-bottom: 5px;">\1</li>', content, flags=re.MULTILINE)
    content = re.sub(r'^(\d+)\. (.*?)$', r'<li style="margin-left: 20px; margin-bottom: 5px;">\2</li>', content, flags=re.MULTILINE)

    # 줄바꿈
    content = content.replace('\n\n', '</p><p>')
    content = f'<p>{content}</p>'

    return content


def create_market_news_payload(report: str, news_items: List[Dict] = None) -> Dict:
    """
    N8N 웹훅으로 보낼 페이로드 생성
    """
    html_content = format_market_news_html(report, news_items)

    return {
        "type": "market_news_report",
        "timestamp": datetime.now().isoformat(),
        "content": html_content,
        "report": html_content,
        "format": "html",
        "subject": f"오늘의 시장 뉴스 - {datetime.now().strftime('%Y년 %m월 %d일')}",
        "recipient_email": None,  # 환경변수에서 가져옴
        "category": "market_news"
    }


# ============================================================================
# 테스트
# ============================================================================

if __name__ == "__main__":
    # 샘플 리포트
    sample_report = """
## 📊 시장 요약
오늘 글로벌 시장은 Fed 금리 관련 뉴스와 반도체 섹터의 호재 소식으로 혼조를 보일 것으로 예상됩니다.

## 🌍 글로벌 시장 (나스닥)
### ⚠️ 높은 영향도
- **Fed 금리 인상 신호**: 달러 강세로 수출주 약세
  추천: 내수주 비중 확대 검토

- **S&P 500 신고가**: 미국 경제 강세 지속
  추천: 유가 상승에 주목

### 🟡 중간 영향도
- Tesla 배터리 기술: 전기차 산업 재편
  추천: 국내 배터리주 모니터링

## 🔧 반도체 뉴스
### ⚠️ 높은 영향도
- **Samsung 3nm 공정 시작**: 장기 긍정 신호
  영향 종목: 삼성전자, SK Hynix
  추천: 해당 종목 매수 기회 검토

- **TSMC 파운드리 호황**: 글로벌 반도체 회복 신호
  영향 종목: 국내 파운드리 관련주
  추천: 관련 supplier 주목

## ⚔️ 지정학적 리스크
### ⚠️ 높은 영향도
- **미중 기술 제재 심화**: 반도체 공급망 우려
  영향 종목: 대기업, 수출주
  추천: 리스크 헤징 강화

## 🇰🇷 국내 뉴스
### ⚠️ 높은 영향도
- **한은 금리 결정 예정**: 내일 결정, 인상 확률 높음
  영향 범위: 금리 민감주 (금융주, 부동산)
  추천: 금리 결정 대기

- **원/달러 환율 상승**: 수출 우호
  영향 범위: 자동차, 전자, 반도체
  추천: 수출주 매수 관심

## 📈 종합 평가
**호재 > 악재** (긍정 신호 강화)

반도체 섹터의 구조적 호재와 수출주 환율 이익이
미국 금리 인상 우려를 상쇄할 것으로 판단됩니다.
"""

    payload = create_market_news_payload(sample_report)
    print("✅ 페이로드 생성 완료")
    print(f"📊 크기: {len(payload['report'])} bytes")
