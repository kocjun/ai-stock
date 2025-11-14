"""
이메일 전송 유틸리티
- Paper Trading 결과 전송
- Red Team 검증 결과 전송
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Dict, List, Optional
import json
from pathlib import Path
from dotenv import load_dotenv

# .env 파일 로드
env_path = Path(__file__).parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)


def send_email(
    subject: str,
    body_html: str,
    to_email: Optional[str] = None,
    from_email: Optional[str] = None,
    smtp_server: Optional[str] = None,
    smtp_port: Optional[int] = None,
    smtp_password: Optional[str] = None
) -> bool:
    """
    이메일 전송

    Args:
        subject: 제목
        body_html: HTML 본문
        to_email: 수신자 (기본값: .env의 EMAIL_TO)
        from_email: 발신자 (기본값: .env의 EMAIL_FROM)
        smtp_server: SMTP 서버 (기본값: .env의 SMTP_SERVER)
        smtp_port: SMTP 포트 (기본값: .env의 SMTP_PORT)
        smtp_password: SMTP 비밀번호 (기본값: .env의 SMTP_PASSWORD)

    Returns:
        성공 여부
    """
    try:
        # 환경 변수에서 기본값 가져오기
        to_email = to_email or os.getenv("EMAIL_TO")
        from_email = from_email or os.getenv("EMAIL_FROM")
        smtp_server = smtp_server or os.getenv("SMTP_SERVER", "smtp.gmail.com")
        smtp_port = smtp_port or int(os.getenv("SMTP_PORT", "587"))
        smtp_password = smtp_password or os.getenv("SMTP_PASSWORD")

        if not all([to_email, from_email, smtp_password]):
            print("❌ 이메일 설정이 불완전합니다. .env 파일을 확인하세요.")
            print(f"   EMAIL_TO: {'✓' if to_email else '✗'}")
            print(f"   EMAIL_FROM: {'✓' if from_email else '✗'}")
            print(f"   SMTP_PASSWORD: {'✓' if smtp_password else '✗'}")
            return False

        # 이메일 메시지 생성
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = from_email
        msg['To'] = to_email

        # HTML 본문 추가
        html_part = MIMEText(body_html, 'html', 'utf-8')
        msg.attach(html_part)

        # SMTP 연결 및 전송
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(from_email, smtp_password)
            server.send_message(msg)

        print(f"✅ 이메일 전송 완료: {to_email}")
        return True

    except Exception as e:
        print(f"❌ 이메일 전송 실패: {e}")
        return False


def format_trading_result_email(result_data: Dict) -> str:
    """
    Paper Trading 결과를 HTML 이메일 형식으로 변환

    Args:
        result_data: trading_workflow_*.json 파일 내용

    Returns:
        HTML 이메일 본문
    """
    import psycopg2

    timestamp = result_data.get('timestamp', 'N/A')
    steps = result_data.get('steps', {})
    final_metrics = result_data.get('final_metrics', {})

    # AI 분석 결과
    ai_analysis = steps.get('ai_analysis', {})
    recommendations = ai_analysis.get('recommendations', [])

    # 매수 실행 결과
    buy_execution = steps.get('buy_execution', {})
    buy_data = buy_execution.get('data', {})
    executed_trades = buy_data.get('executed_trades', [])

    # 스냅샷 정보
    snapshot = steps.get('snapshot', {})
    snapshot_data = snapshot.get('data', {})

    # 날짜 포맷팅
    try:
        dt = datetime.fromisoformat(timestamp)
        date_str = dt.strftime('%Y년 %m월 %d일 %H:%M')
    except:
        date_str = timestamp

    # 데이터베이스에서 종목명 조회
    stock_names = {}
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432"),
            database=os.getenv("DB_NAME", "investment_db"),
            user=os.getenv("DB_USER", "invest_user"),
            password=os.getenv("DB_PASSWORD", "invest_pass_2024!")
        )
        cur = conn.cursor()
        cur.execute("SELECT code, name FROM stocks")
        for code, name in cur.fetchall():
            stock_names[code] = name
        cur.close()
        conn.close()
    except:
        pass

    # AI 추천 종목 테이블
    rec_rows = ""
    if recommendations:
        for rec in recommendations:
            code = rec.get('code', 'N/A')
            name = stock_names.get(code, code)
            weight = rec.get('weight', 0) * 100
            rec_rows += f"""
            <tr>
                <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">{code}</td>
                <td style="padding: 10px; border: 1px solid #ddd;">{name}</td>
                <td style="padding: 10px; border: 1px solid #ddd; text-align: right; font-weight: bold;">{weight:.1f}%</td>
            </tr>
            """
    else:
        rec_rows = '<tr><td colspan="3" style="padding: 10px; text-align: center; color: #999;">추천 종목 없음</td></tr>'

    # 실제 매수 종목 테이블
    trade_rows = ""
    total_invested = 0
    if executed_trades:
        for trade in executed_trades:
            code = trade.get('code', 'N/A')
            name = stock_names.get(code, code)
            quantity = trade.get('quantity', 0)
            price = trade.get('price', 0)
            amount = trade.get('amount', 0)
            total_invested += amount
            trade_rows += f"""
            <tr>
                <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">{code}</td>
                <td style="padding: 10px; border: 1px solid #ddd;">{name}</td>
                <td style="padding: 10px; border: 1px solid #ddd; text-align: right;">{quantity:,}주</td>
                <td style="padding: 10px; border: 1px solid #ddd; text-align: right;">{price:,.0f}원</td>
                <td style="padding: 10px; border: 1px solid #ddd; text-align: right; font-weight: bold;">{amount:,.0f}원</td>
            </tr>
            """
    else:
        trade_rows = '<tr><td colspan="5" style="padding: 10px; text-align: center; color: #999;">거래 없음</td></tr>'

    # 포트폴리오 현황
    total_value = snapshot_data.get('total_value', 0)
    cash = snapshot_data.get('cash_balance', 0)
    stock_value = snapshot_data.get('stock_value', 0)
    return_pct = snapshot_data.get('return_pct', 0)

    # 최종 성과
    initial_balance = final_metrics.get('initial_balance', 10000000)
    total_return = final_metrics.get('total_return', 0)
    num_trades = final_metrics.get('num_trades', 0)

    # 수익률 색상
    return_color = "#10b981" if return_pct >= 0 else "#ef4444"
    return_sign = "+" if return_pct >= 0 else ""

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: 'Malgun Gothic', 'Apple SD Gothic Neo', Arial, sans-serif; line-height: 1.6; color: #333; background: #f5f7fa; margin: 0; padding: 0; }}
            .container {{ max-width: 900px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 40px 30px; border-radius: 12px; margin-bottom: 25px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
            .header h1 {{ margin: 0 0 10px 0; font-size: 32px; font-weight: 700; }}
            .header p {{ margin: 0; opacity: 0.95; font-size: 16px; }}
            .section {{ background: white; padding: 25px; margin-bottom: 20px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }}
            .section h2 {{ color: #667eea; margin: 0 0 20px 0; border-bottom: 3px solid #667eea; padding-bottom: 12px; font-size: 22px; }}
            .stats {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-top: 20px; }}
            .stat-box {{ text-align: center; padding: 20px; background: linear-gradient(135deg, #f5f7fa 0%, #e8ecf1 100%); border-radius: 10px; border: 2px solid #e1e8ed; }}
            .stat-value {{ font-size: 26px; font-weight: bold; color: #667eea; margin-bottom: 8px; }}
            .stat-label {{ font-size: 13px; color: #666; text-transform: uppercase; letter-spacing: 0.5px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
            th {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 14px 12px; text-align: left; font-size: 14px; font-weight: 600; }}
            td {{ padding: 12px; border: 1px solid #e1e8ed; font-size: 14px; }}
            tr:nth-child(even) {{ background-color: #f9fafb; }}
            tr:hover {{ background-color: #f0f4f8; }}
            .highlight {{ background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 15px 0; border-radius: 6px; }}
            .success {{ background: #d4edda; border-left: 4px solid #28a745; padding: 15px; margin: 15px 0; border-radius: 6px; }}
            .footer {{ text-align: center; color: #999; font-size: 12px; margin-top: 40px; padding-top: 25px; border-top: 2px solid #e1e8ed; }}
            .footer p {{ margin: 5px 0; }}
            .badge {{ display: inline-block; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 600; }}
            .badge-success {{ background: #d4edda; color: #155724; }}
            .badge-warning {{ background: #fff3cd; color: #856404; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📊 Paper Trading 일일 리포트</h1>
                <p>{date_str}</p>
            </div>

            <div class="section">
                <h2>💰 포트폴리오 현황</h2>
                <div class="stats">
                    <div class="stat-box">
                        <div class="stat-value">{total_value:,.0f}원</div>
                        <div class="stat-label">총 자산</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-value">{stock_value:,.0f}원</div>
                        <div class="stat-label">주식 평가액</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-value">{cash:,.0f}원</div>
                        <div class="stat-label">현금 잔액</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-value" style="color: {return_color};">{return_sign}{return_pct:.2f}%</div>
                        <div class="stat-label">수익률</div>
                    </div>
                </div>
                <div class="highlight">
                    <strong>💡 투자 현황:</strong> 초기 자본 {initial_balance:,.0f}원에서 {len(executed_trades)}건의 거래를 통해 {total_invested:,.0f}원 투자 ({(total_invested/initial_balance*100):.1f}%)
                </div>
            </div>

            <div class="section">
                <h2>🎯 AI 추천 종목 ({len(recommendations)}개)</h2>
                <table>
                    <thead>
                        <tr>
                            <th>종목코드</th>
                            <th>종목명</th>
                            <th style="text-align: right;">추천 비중</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rec_rows}
                    </tbody>
                </table>
            </div>

            <div class="section">
                <h2>✅ 실제 매수 내역 ({len(executed_trades)}건)</h2>
                <table>
                    <thead>
                        <tr>
                            <th>종목코드</th>
                            <th>종목명</th>
                            <th style="text-align: right;">수량</th>
                            <th style="text-align: right;">매수가</th>
                            <th style="text-align: right;">투자금액</th>
                        </tr>
                    </thead>
                    <tbody>
                        {trade_rows}
                    </tbody>
                </table>
                <div class="success" style="margin-top: 20px;">
                    <strong>✅ 매수 완료:</strong> {len(executed_trades)}개 종목, 총 {total_invested:,.0f}원 투자 완료
                </div>
            </div>

            <div class="section">
                <h2>📈 성과 요약</h2>
                <table>
                    <tr>
                        <td style="font-weight: bold; background: #f5f7fa;">초기 자본</td>
                        <td style="text-align: right;">{initial_balance:,.0f}원</td>
                    </tr>
                    <tr>
                        <td style="font-weight: bold; background: #f5f7fa;">현재 총 자산</td>
                        <td style="text-align: right; font-weight: bold;">{total_value:,.0f}원</td>
                    </tr>
                    <tr>
                        <td style="font-weight: bold; background: #f5f7fa;">손익</td>
                        <td style="text-align: right; font-weight: bold; color: {return_color};">{return_sign}{total_return:,.0f}원 ({return_sign}{return_pct:.2f}%)</td>
                    </tr>
                    <tr>
                        <td style="font-weight: bold; background: #f5f7fa;">총 거래 건수</td>
                        <td style="text-align: right;">{num_trades}건</td>
                    </tr>
                    <tr>
                        <td style="font-weight: bold; background: #f5f7fa;">현금 보유율</td>
                        <td style="text-align: right;">{(cash/total_value*100):.1f}%</td>
                    </tr>
                </table>
            </div>

            <div class="footer">
                <p><strong>🤖 AI 주식 투자 시스템</strong> | Paper Trading Mode</p>
                <p>이 이메일은 자동으로 생성되었습니다.</p>
                <p style="margin-top: 10px; color: #666;">다음 리포트: 내일 오전 10시 (평일)</p>
            </div>
        </div>
    </body>
    </html>
    """

    return html


def format_redteam_result_email(result_data: Dict) -> str:
    """
    Red Team 검증 결과를 HTML 이메일 형식으로 변환

    Args:
        result_data: 검증 결과 데이터

    Returns:
        HTML 이메일 본문
    """
    timestamp = result_data.get('timestamp', 'N/A')
    comparison = result_data.get('comparison', {})

    # 날짜 포맷팅
    try:
        dt = datetime.fromisoformat(timestamp)
        date_str = dt.strftime('%Y년 %m월 %d일 %H:%M')
    except:
        date_str = timestamp

    # 검증 결과
    agreement_rate = comparison.get('agreement_rate', 0) * 100
    agreed_stocks = comparison.get('agreed_stocks', [])
    local_only = comparison.get('local_only_stocks', [])
    redteam_only = comparison.get('redteam_only_stocks', [])
    recommendation = comparison.get('recommendation', 'N/A')

    # 일치율에 따른 색상
    if agreement_rate >= 80:
        color = "#10b981"  # 녹색
        status = "✅ 우수"
    elif agreement_rate >= 50:
        color = "#f59e0b"  # 주황색
        status = "⚠️ 주의"
    else:
        color = "#ef4444"  # 빨간색
        status = "❌ 불일치"

    # 일치 종목 리스트
    agreed_list = ", ".join(agreed_stocks) if agreed_stocks else "없음"
    local_list = ", ".join(local_only) if local_only else "없음"
    redteam_list = ", ".join(redteam_only) if redteam_only else "없음"

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: 'Malgun Gothic', Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 800px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 20px; }}
            .header h1 {{ margin: 0; font-size: 28px; }}
            .header p {{ margin: 5px 0 0 0; opacity: 0.9; }}
            .section {{ background: white; padding: 20px; margin-bottom: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
            .section h2 {{ color: #f5576c; margin-top: 0; border-bottom: 2px solid #f5576c; padding-bottom: 10px; }}
            .agreement-box {{ text-align: center; padding: 30px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 10px; color: white; margin: 20px 0; }}
            .agreement-rate {{ font-size: 48px; font-weight: bold; }}
            .agreement-status {{ font-size: 24px; margin-top: 10px; }}
            .stock-list {{ background: #f5f7fa; padding: 15px; border-radius: 8px; margin: 10px 0; }}
            .stock-list h3 {{ margin-top: 0; color: #667eea; }}
            .recommendation {{ background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0; }}
            .footer {{ text-align: center; color: #999; font-size: 12px; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔍 Red Team 검증 리포트</h1>
                <p>{date_str}</p>
            </div>

            <div class="agreement-box" style="background: {color};">
                <div class="agreement-rate">{agreement_rate:.1f}%</div>
                <div class="agreement-status">{status}</div>
                <div style="margin-top: 10px; opacity: 0.9;">로컬 LLM vs OpenAI 일치율</div>
            </div>

            <div class="section">
                <h2>📊 상세 비교 결과</h2>

                <div class="stock-list">
                    <h3>✅ 일치하는 종목 ({len(agreed_stocks)}개)</h3>
                    <p>{agreed_list}</p>
                </div>

                <div class="stock-list">
                    <h3>🔵 로컬 LLM만 추천 ({len(local_only)}개)</h3>
                    <p>{local_list}</p>
                </div>

                <div class="stock-list">
                    <h3>🔴 OpenAI만 추천 ({len(redteam_only)}개)</h3>
                    <p>{redteam_list}</p>
                </div>
            </div>

            <div class="section">
                <h2>💡 권장 사항</h2>
                <div class="recommendation">
                    <strong>📌 {recommendation}</strong>
                </div>
            </div>

            <div class="footer">
                <p>🤖 AI 주식 투자 시스템 | Red Team Validation</p>
                <p>이 이메일은 매주 토요일 자동으로 생성됩니다.</p>
            </div>
        </div>
    </body>
    </html>
    """

    return html


def send_trading_result_email(result_file_path: str) -> bool:
    """
    Paper Trading 결과 이메일 전송

    Args:
        result_file_path: trading_workflow_*.json 파일 경로

    Returns:
        성공 여부
    """
    try:
        with open(result_file_path, 'r', encoding='utf-8') as f:
            result_data = json.load(f)

        subject = f"[Paper Trading] 일일 리포트 - {datetime.now().strftime('%Y-%m-%d')}"
        body_html = format_trading_result_email(result_data)

        return send_email(subject, body_html)

    except Exception as e:
        print(f"❌ Trading 결과 이메일 전송 실패: {e}")
        return False


def send_redteam_result_email(result_file_path: str) -> bool:
    """
    Red Team 검증 결과 이메일 전송

    Args:
        result_file_path: redteam_validation_*.json 파일 경로

    Returns:
        성공 여부
    """
    try:
        with open(result_file_path, 'r', encoding='utf-8') as f:
            result_data = json.load(f)

        subject = f"[Red Team] 주간 검증 리포트 - {datetime.now().strftime('%Y-%m-%d')}"
        body_html = format_redteam_result_email(result_data)

        return send_email(subject, body_html)

    except Exception as e:
        print(f"❌ Red Team 결과 이메일 전송 실패: {e}")
        return False


if __name__ == "__main__":
    # 테스트용
    print("이메일 전송 유틸리티")
    print("실제 전송은 run_paper_trading.sh 또는 run_redteam_validation.sh에서 자동으로 실행됩니다.")
