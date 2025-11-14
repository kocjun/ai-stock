"""
성과 보고서 생성 모듈

일간/주간/월간 투자 성과 분석 및 보고서 생성
"""

import sys
import os
import requests
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np

# 프로젝트 루트 경로 추가 (Cron 실행 시에도 작동하도록 우선순위 높임)
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(Path(__file__).parent))  # paper_trading 디렉토리 추가

# Cron/터미널 모두에서 작동하도록 절대 import 사용
try:
    from core.utils.db_utils import get_db_connection
    from paper_trading.portfolio_manager import (
        get_portfolio_history, calculate_portfolio_metrics,
        get_trade_history
    )
    from paper_trading.paper_trading import get_portfolio
except ImportError:
    # paper_trading 디렉토리에서 직접 실행하는 경우 대비
    from portfolio_manager import (
        get_portfolio_history, calculate_portfolio_metrics,
        get_trade_history
    )
    from paper_trading import get_portfolio
    import sys
    sys.path.insert(0, str(project_root))
    from core.utils.db_utils import get_db_connection


def calculate_sharpe_ratio(returns: List[float], risk_free_rate: float = 0.03) -> float:
    """
    Sharpe Ratio 계산

    Args:
        returns: 일별 수익률 리스트
        risk_free_rate: 무위험 수익률 (연율, 기본: 3%)

    Returns:
        float: Sharpe Ratio
    """
    if len(returns) < 2:
        return 0.0

    returns_array = np.array(returns)
    excess_returns = returns_array - (risk_free_rate / 252)  # 일별 무위험 수익률

    if np.std(excess_returns) == 0:
        return 0.0

    sharpe = np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(252)
    return float(sharpe)


def calculate_max_drawdown(values: List[float]) -> Tuple[float, int]:
    """
    Maximum Drawdown (MDD) 계산

    Args:
        values: 일별 자산 가치 리스트

    Returns:
        Tuple[float, int]: (MDD %, 최대 낙폭 지속 일수)
    """
    if len(values) < 2:
        return 0.0, 0

    values_array = np.array(values)
    cummax = np.maximum.accumulate(values_array)
    drawdown = (values_array - cummax) / cummax * 100

    mdd = float(np.min(drawdown))

    # 최대 낙폭 지속 일수
    max_dd_days = 0
    current_dd_days = 0

    for dd in drawdown:
        if dd < 0:
            current_dd_days += 1
            max_dd_days = max(max_dd_days, current_dd_days)
        else:
            current_dd_days = 0

    return mdd, max_dd_days


def calculate_volatility(returns: List[float]) -> float:
    """
    변동성 계산 (연율)

    Args:
        returns: 일별 수익률 리스트

    Returns:
        float: 연율 변동성 (%)
    """
    if len(returns) < 2:
        return 0.0

    return float(np.std(returns) * np.sqrt(252) * 100)


def generate_performance_report(account_id: int, period_days: int = 7,
                                report_type: str = "weekly") -> Dict:
    """
    성과 보고서 생성

    Args:
        account_id: 계좌 ID
        period_days: 분석 기간 (일)
        report_type: 보고서 유형 (daily/weekly/monthly)

    Returns:
        Dict: 보고서 데이터
    """
    # 기본 메트릭
    metrics = calculate_portfolio_metrics(account_id)

    # 포트폴리오 히스토리
    history = get_portfolio_history(account_id, period_days)

    # 일별 수익률 계산
    daily_returns = []
    if len(history) > 1:
        for i in range(len(history) - 1):
            prev_value = history[i+1]['total_value']  # 역순이므로
            curr_value = history[i]['total_value']
            if prev_value > 0:
                daily_return = (curr_value - prev_value) / prev_value
                daily_returns.append(daily_return)

    # 자산 가치 리스트
    total_values = [h['total_value'] for h in reversed(history)]

    # 고급 지표 계산
    sharpe_ratio = calculate_sharpe_ratio(daily_returns) if daily_returns else 0.0
    max_drawdown, mdd_days = calculate_max_drawdown(total_values) if total_values else (0.0, 0)
    volatility = calculate_volatility(daily_returns) if daily_returns else 0.0

    # 현재 포트폴리오
    portfolio = get_portfolio(account_id)

    # 거래 히스토리
    trades = get_trade_history(account_id, limit=period_days * 5)  # 기간 내 거래

    # 보고서 데이터
    report = {
        'report_type': report_type,
        'period_days': period_days,
        'generated_at': datetime.now().isoformat(),

        # 기본 정보
        'account_id': account_id,
        'initial_balance': metrics['initial_balance'],
        'current_value': metrics['total_value'],
        'cash_balance': portfolio['cash_balance'],
        'stock_value': portfolio['total_stock_value'],

        # 수익 지표
        'total_return': metrics['total_return'],
        'total_return_pct': metrics['total_return_pct'],

        # 거래 통계
        'num_trades': metrics['num_trades'],
        'num_positions': portfolio['num_positions'],
        'win_rate': metrics['win_rate'],
        'avg_profit_per_trade': metrics['avg_profit_per_trade'],

        # 리스크 지표
        'sharpe_ratio': sharpe_ratio,
        'max_drawdown': max_drawdown,
        'mdd_days': mdd_days,
        'volatility': volatility,

        # 상세 데이터
        'positions': portfolio['positions'],
        'recent_trades': trades[:10],  # 최근 10개 거래
        'daily_history': history[:period_days]
    }

    return report


def format_html_report(report: Dict) -> str:
    """
    보고서를 HTML 이메일 형식으로 포맷팅

    Args:
        report: 보고서 데이터

    Returns:
        str: HTML 텍스트
    """
    # 보고서 유형 이름
    report_type_name = {
        'daily': '일간',
        'weekly': '주간',
        'monthly': '월간'
    }.get(report['report_type'], '투자')

    # 날짜 포맷팅
    try:
        generated_at = datetime.fromisoformat(report['generated_at'])
        date_str = generated_at.strftime('%Y년 %m월 %d일 %H:%M')
    except:
        date_str = report['generated_at']

    # 수익률 색상
    return_pct = report.get('total_return_pct', 0)
    return_color = "#10b981" if return_pct >= 0 else "#ef4444"
    return_sign = "+" if return_pct >= 0 else ""

    # 포지션 테이블
    positions_rows = ""
    if report.get('positions'):
        for pos in report['positions']:
            profit_loss = pos.get('profit_loss', 0)
            profit_loss_pct = pos.get('profit_loss_pct', 0)
            profit_color = "#10b981" if profit_loss >= 0 else "#ef4444"
            profit_sign = "+" if profit_loss >= 0 else ""

            positions_rows += f"""
            <tr>
                <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">{pos.get('code', 'N/A')}</td>
                <td style="padding: 10px; border: 1px solid #ddd;">{pos.get('name', 'N/A')}</td>
                <td style="padding: 10px; border: 1px solid #ddd; text-align: right;">{pos.get('quantity', 0):,}주</td>
                <td style="padding: 10px; border: 1px solid #ddd; text-align: right;">{pos.get('avg_price', 0):,.0f}원</td>
                <td style="padding: 10px; border: 1px solid #ddd; text-align: right;">{pos.get('current_price', 0):,.0f}원</td>
                <td style="padding: 10px; border: 1px solid #ddd; text-align: right; color: {profit_color};">{profit_sign}{profit_loss:,.0f}원</td>
                <td style="padding: 10px; border: 1px solid #ddd; text-align: right; color: {profit_color};">{profit_sign}{profit_loss_pct:.2f}%</td>
            </tr>
            """
    else:
        positions_rows = '<tr><td colspan="7" style="padding: 10px; text-align: center; color: #999;">보유 종목 없음</td></tr>'

    # 최근 거래 테이블
    trades_rows = ""
    if report.get('recent_trades'):
        for trade in report['recent_trades'][:10]:
            trade_type = "매수" if trade.get('trade_type') == 'buy' else "매도"
            trade_date = trade.get('trade_date', 'N/A')[:10]

            trades_rows += f"""
            <tr>
                <td style="padding: 10px; border: 1px solid #ddd;">{trade_date}</td>
                <td style="padding: 10px; border: 1px solid #ddd;">{trade_type}</td>
                <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">{trade.get('code', 'N/A')}</td>
                <td style="padding: 10px; border: 1px solid #ddd;">{trade.get('stock_name', 'N/A')}</td>
                <td style="padding: 10px; border: 1px solid #ddd; text-align: right;">{trade.get('quantity', 0):,}주</td>
                <td style="padding: 10px; border: 1px solid #ddd; text-align: right;">{trade.get('price', 0):,.0f}원</td>
                <td style="padding: 10px; border: 1px solid #ddd; text-align: right; font-weight: bold;">{trade.get('total_amount', 0):,.0f}원</td>
            </tr>
            """
    else:
        trades_rows = '<tr><td colspan="7" style="padding: 10px; text-align: center; color: #999;">거래 내역 없음</td></tr>'

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ font-family: 'Malgun Gothic', 'Apple SD Gothic Neo', Arial, sans-serif; line-height: 1.6; color: #333; background: #f5f7fa; margin: 0; padding: 0; }}
            .container {{ max-width: 900px; margin: 0 auto; padding: 15px; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px 20px; border-radius: 12px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
            .header h1 {{ margin: 0 0 10px 0; font-size: 28px; font-weight: 700; }}
            .header p {{ margin: 0; opacity: 0.95; font-size: 14px; }}
            .section {{ background: white; padding: 20px; margin-bottom: 15px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }}
            .section h2 {{ color: #667eea; margin: 0 0 15px 0; border-bottom: 3px solid #667eea; padding-bottom: 10px; font-size: 20px; }}
            .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 12px; margin-top: 15px; }}
            .stat-box {{ text-align: center; padding: 15px; background: linear-gradient(135deg, #f5f7fa 0%, #e8ecf1 100%); border-radius: 10px; border: 2px solid #e1e8ed; }}
            .stat-value {{ font-size: 22px; font-weight: bold; color: #667eea; margin-bottom: 8px; word-break: break-word; }}
            .stat-label {{ font-size: 11px; color: #666; text-transform: uppercase; letter-spacing: 0.5px; }}

            /* 테이블 반응형 스타일 */
            table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
            th {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 12px 8px; text-align: left; font-size: 13px; font-weight: 600; }}
            td {{ padding: 10px 8px; border: 1px solid #e1e8ed; font-size: 13px; }}
            tr:nth-child(even) {{ background-color: #f9fafb; }}

            .footer {{ text-align: center; color: #999; font-size: 11px; margin-top: 30px; padding-top: 20px; border-top: 2px solid #e1e8ed; }}
            .footer p {{ margin: 4px 0; }}

            /* 모바일 반응형 (@600px 이하) */
            @media (max-width: 768px) {{
                .container {{ padding: 10px; }}
                .header {{ padding: 20px 15px; margin-bottom: 15px; }}
                .header h1 {{ font-size: 24px; margin-bottom: 8px; }}
                .header p {{ font-size: 12px; }}
                .section {{ padding: 15px; margin-bottom: 12px; }}
                .section h2 {{ font-size: 18px; margin-bottom: 12px; padding-bottom: 8px; }}
                .stats {{ grid-template-columns: repeat(2, 1fr); gap: 10px; }}
                .stat-box {{ padding: 12px; }}
                .stat-value {{ font-size: 18px; }}
                .stat-label {{ font-size: 10px; }}

                /* 모바일에서 테이블 스크롤 */
                table {{ font-size: 12px; }}
                th {{ padding: 10px 6px; font-size: 11px; }}
                td {{ padding: 8px 6px; }}

                .footer {{ margin-top: 20px; padding-top: 15px; font-size: 10px; }}
            }}

            /* 매우 작은 모바일 (@480px 이하) */
            @media (max-width: 480px) {{
                .container {{ padding: 8px; }}
                .header {{ padding: 15px 12px; margin-bottom: 12px; }}
                .header h1 {{ font-size: 20px; margin-bottom: 6px; }}
                .header p {{ font-size: 11px; }}
                .section {{ padding: 12px; margin-bottom: 10px; }}
                .section h2 {{ font-size: 16px; margin-bottom: 10px; padding-bottom: 6px; }}
                .stats {{ grid-template-columns: 1fr; gap: 8px; }}
                .stat-box {{ padding: 10px; }}
                .stat-value {{ font-size: 16px; }}
                .stat-label {{ font-size: 9px; }}

                /* 매우 좁은 테이블 처리 */
                table {{ font-size: 11px; }}
                th {{ padding: 8px 4px; font-size: 10px; }}
                td {{ padding: 6px 4px; }}

                .footer {{ margin-top: 15px; padding-top: 10px; font-size: 9px; }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📊 {report_type_name} 투자 성과 보고서</h1>
                <p>{date_str}</p>
            </div>

            <div class="section">
                <h2>💰 자산 현황</h2>
                <div class="stats">
                    <div class="stat-box">
                        <div class="stat-value">{report.get('current_value', 0):,.0f}원</div>
                        <div class="stat-label">총 자산</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-value">{report.get('stock_value', 0):,.0f}원</div>
                        <div class="stat-label">주식 평가액</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-value">{report.get('cash_balance', 0):,.0f}원</div>
                        <div class="stat-label">현금 잔액</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-value" style="color: {return_color};">{return_sign}{return_pct:.2f}%</div>
                        <div class="stat-label">수익률</div>
                    </div>
                </div>
            </div>

            <div class="section">
                <h2>📈 성과 지표</h2>
                <table>
                    <tr>
                        <td style="font-weight: bold; background: #f5f7fa;">초기 자본</td>
                        <td style="text-align: right;">{report.get('initial_balance', 0):,.0f}원</td>
                    </tr>
                    <tr>
                        <td style="font-weight: bold; background: #f5f7fa;">현재 총 자산</td>
                        <td style="text-align: right; font-weight: bold;">{report.get('current_value', 0):,.0f}원</td>
                    </tr>
                    <tr>
                        <td style="font-weight: bold; background: #f5f7fa;">손익</td>
                        <td style="text-align: right; font-weight: bold; color: {return_color};">{return_sign}{report.get('total_return', 0):,.0f}원 ({return_sign}{return_pct:.2f}%)</td>
                    </tr>
                    <tr>
                        <td style="font-weight: bold; background: #f5f7fa;">Sharpe Ratio</td>
                        <td style="text-align: right;">{report.get('sharpe_ratio', 0):.2f}</td>
                    </tr>
                    <tr>
                        <td style="font-weight: bold; background: #f5f7fa;">최대 낙폭 (MDD)</td>
                        <td style="text-align: right;">{report.get('max_drawdown', 0):.2f}%</td>
                    </tr>
                    <tr>
                        <td style="font-weight: bold; background: #f5f7fa;">변동성 (연율)</td>
                        <td style="text-align: right;">{report.get('volatility', 0):.2f}%</td>
                    </tr>
                    <tr>
                        <td style="font-weight: bold; background: #f5f7fa;">승률</td>
                        <td style="text-align: right;">{report.get('win_rate', 0):.1f}%</td>
                    </tr>
                    <tr>
                        <td style="font-weight: bold; background: #f5f7fa;">총 거래 횟수</td>
                        <td style="text-align: right;">{report.get('num_trades', 0)}회</td>
                    </tr>
                    <tr>
                        <td style="font-weight: bold; background: #f5f7fa;">보유 종목 수</td>
                        <td style="text-align: right;">{report.get('num_positions', 0)}개</td>
                    </tr>
                    <tr>
                        <td style="font-weight: bold; background: #f5f7fa;">평균 거래당 수익</td>
                        <td style="text-align: right;">{report.get('avg_profit_per_trade', 0):,.0f}원</td>
                    </tr>
                </table>
            </div>

            <div class="section">
                <h2>💼 현재 포트폴리오 ({report.get('num_positions', 0)}개 종목)</h2>
                <table>
                    <thead>
                        <tr>
                            <th>종목코드</th>
                            <th>종목명</th>
                            <th style="text-align: right;">수량</th>
                            <th style="text-align: right;">평균가</th>
                            <th style="text-align: right;">현재가</th>
                            <th style="text-align: right;">손익</th>
                            <th style="text-align: right;">수익률</th>
                        </tr>
                    </thead>
                    <tbody>
                        {positions_rows}
                    </tbody>
                </table>
            </div>

            <div class="section">
                <h2>📋 최근 거래 내역</h2>
                <table>
                    <thead>
                        <tr>
                            <th>날짜</th>
                            <th>구분</th>
                            <th>종목코드</th>
                            <th>종목명</th>
                            <th style="text-align: right;">수량</th>
                            <th style="text-align: right;">가격</th>
                            <th style="text-align: right;">금액</th>
                        </tr>
                    </thead>
                    <tbody>
                        {trades_rows}
                    </tbody>
                </table>
            </div>

            <div class="footer">
                <p><strong>🤖 AI 주식 투자 시스템</strong> | {report_type_name} 성과 보고서</p>
                <p>이 이메일은 자동으로 생성되었습니다.</p>
                <p style="margin-top: 10px; color: #666;">다음 리포트: {('내일 오전' if report['report_type'] == 'daily' else '다음주 오전')}</p>
            </div>
        </div>
    </body>
    </html>
    """

    return html


def format_markdown_report(report: Dict) -> str:
    """
    보고서를 마크다운 형식으로 포맷팅

    Args:
        report: 보고서 데이터

    Returns:
        str: 마크다운 텍스트
    """
    md = []

    # 헤더
    report_type_name = {
        'daily': '일간',
        'weekly': '주간',
        'monthly': '월간'
    }.get(report['report_type'], '투자')

    md.append(f"# 📊 {report_type_name} 투자 성과 보고서\n")
    md.append(f"**생성 일시**: {datetime.fromisoformat(report['generated_at']).strftime('%Y-%m-%d %H:%M:%S')}")
    md.append(f"**분석 기간**: 최근 {report['period_days']}일\n")
    md.append("---\n")

    # 1. 요약
    md.append("## 💰 자산 현황\n")
    md.append(f"- **초기 자금**: {report['initial_balance']:,.0f}원")
    md.append(f"- **현재 총 자산**: {report['current_value']:,.0f}원")
    md.append(f"  - 현금: {report['cash_balance']:,.0f}원")
    md.append(f"  - 주식: {report['stock_value']:,.0f}원")
    md.append(f"- **총 수익**: {report['total_return']:+,.0f}원 ({report['total_return_pct']:+.2f}%)")
    md.append("")

    # 2. 성과 지표
    md.append("## 📈 성과 지표\n")
    md.append("| 지표 | 값 |")
    md.append("|------|------|")
    md.append(f"| 수익률 | {report['total_return_pct']:+.2f}% |")
    md.append(f"| Sharpe Ratio | {report['sharpe_ratio']:.2f} |")
    md.append(f"| 최대 낙폭 (MDD) | {report['max_drawdown']:.2f}% |")
    md.append(f"| 변동성 (연율) | {report['volatility']:.2f}% |")
    md.append(f"| 승률 | {report['win_rate']:.1f}% |")
    md.append("")

    # 3. 거래 통계
    md.append("## 📊 거래 통계\n")
    md.append(f"- **총 거래 횟수**: {report['num_trades']}회")
    md.append(f"- **보유 종목 수**: {report['num_positions']}개")
    md.append(f"- **평균 거래당 수익**: {report['avg_profit_per_trade']:,.0f}원")
    md.append("")

    # 4. 현재 포트폴리오
    if report['positions']:
        md.append("## 💼 현재 포트폴리오\n")
        md.append("| 종목 | 수량 | 평균가 | 현재가 | 평가액 | 손익 | 수익률 |")
        md.append("|------|------|--------|--------|--------|------|--------|")

        for pos in report['positions']:
            md.append(
                f"| {pos['name']}<br>({pos['code']}) | {pos['quantity']:,}주 | "
                f"{pos['avg_price']:,.0f}원 | {pos['current_price']:,.0f}원 | "
                f"{pos['current_value']:,.0f}원 | {pos['profit_loss']:+,.0f}원 | "
                f"{pos['profit_loss_pct']:+.2f}% |"
            )
        md.append("")

    # 5. 최근 거래
    if report['recent_trades']:
        md.append("## 📋 최근 거래 내역\n")
        md.append("| 날짜 | 구분 | 종목 | 수량 | 가격 | 금액 |")
        md.append("|------|------|------|------|------|------|")

        for trade in report['recent_trades'][:5]:  # 최근 5개만
            trade_type = "매수" if trade['trade_type'] == 'buy' else "매도"
            date_str = trade['trade_date'][:10]
            md.append(
                f"| {date_str} | {trade_type} | {trade['stock_name']}<br>({trade['code']}) | "
                f"{trade['quantity']:,}주 | {trade['price']:,.0f}원 | {trade['total_amount']:,.0f}원 |"
            )
        md.append("")

    # 6. 면책 조항
    md.append("---\n")
    md.append("## ⚠️ 유의사항\n")
    md.append("- 본 보고서는 페이퍼 트레이딩 시뮬레이션 결과입니다")
    md.append("- 실제 투자 시 슬리피지, 유동성 등의 요인으로 결과가 다를 수 있습니다")
    md.append("- 과거 성과가 미래 수익을 보장하지 않습니다")
    md.append("- 모든 투자 판단과 결과는 투자자 본인의 책임입니다")

    return "\n".join(md)


def save_report_to_db(account_id: int, report: Dict, report_content: str) -> int:
    """
    보고서를 데이터베이스에 저장

    Args:
        account_id: 계좌 ID
        report: 보고서 데이터
        report_content: 보고서 텍스트 내용

    Returns:
        int: 보고서 ID
    """
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            INSERT INTO virtual_reports (
                account_id,
                report_type,
                total_value,
                cash_balance,
                stock_value,
                total_return,
                return_pct,
                num_positions,
                num_trades,
                win_rate,
                avg_profit_per_trade,
                max_drawdown,
                sharpe_ratio,
                report_content
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING report_id
        """, (
            account_id,
            report['report_type'],
            report['current_value'],
            report['cash_balance'],
            report['stock_value'],
            report['total_return'],
            report['total_return_pct'],
            report['num_positions'],
            report['num_trades'],
            report['win_rate'],
            report['avg_profit_per_trade'],
            report['max_drawdown'],
            report['sharpe_ratio'],
            report_content
        ))

        report_id = cur.fetchone()[0]
        conn.commit()

        return report_id

    finally:
        cur.close()
        conn.close()


def send_report_to_n8n(report_content: str, webhook_url: Optional[str] = None, is_html: bool = True, subject: str = None, recipient_email: str = None) -> bool:
    """
    n8n 웹훅으로 보고서 전송

    Args:
        report_content: 보고서 내용
        webhook_url: n8n 웹훅 URL
        is_html: HTML 형식 여부 (기본값: True)
        subject: 이메일 제목
        recipient_email: 수신자 이메일 주소

    Returns:
        bool: 전송 성공 여부
    """
    if webhook_url is None:
        webhook_url = os.getenv("N8N_WEBHOOK_URL")

    if not webhook_url:
        print("⚠️  N8N_WEBHOOK_URL이 설정되지 않았습니다")
        return False

    try:
        payload = {
            "type": "performance_report",
            "timestamp": datetime.now().isoformat(),
            "content": report_content,
            "report": report_content,  # 호환성을 위해 두 필드 모두 포함
            "format": "html" if is_html else "markdown",
            "subject": subject or "투자 성과 보고서",
            "recipient_email": recipient_email or os.getenv("REPORT_EMAIL_RECIPIENT")
        }

        response = requests.post(webhook_url, json=payload, timeout=10)
        response.raise_for_status()

        print(f"✅ n8n 전송 성공: {response.status_code}")
        return True

    except Exception as e:
        print(f"❌ n8n 전송 실패: {e}")
        return False


if __name__ == "__main__":
    """메인 실행"""
    import argparse

    parser = argparse.ArgumentParser(description="성과 보고서 생성")
    parser.add_argument("--account-id", type=int, default=1, help="계좌 ID")
    parser.add_argument("--type", choices=["daily", "weekly", "monthly"],
                        default="weekly", help="보고서 유형")
    parser.add_argument("--days", type=int, help="분석 기간 (일, 미지정시 자동)")
    parser.add_argument("--output", help="출력 파일 경로 (.md)")
    parser.add_argument("--save-db", action="store_true", help="데이터베이스에 저장")
    parser.add_argument("--send-n8n", action="store_true", help="n8n으로 전송")

    args = parser.parse_args()

    # 기간 설정
    if args.days:
        period_days = args.days
    else:
        period_days = {
            'daily': 1,
            'weekly': 7,
            'monthly': 30
        }[args.type]

    print(f"\n{'='*60}")
    print(f"{args.type.upper()} 보고서 생성 중...")
    print(f"{'='*60}\n")

    try:
        # 보고서 생성
        report = generate_performance_report(
            account_id=args.account_id,
            period_days=period_days,
            report_type=args.type
        )

        # 마크다운 포맷팅 (파일 저장용)
        markdown_report = format_markdown_report(report)

        # HTML 포맷팅 (이메일용)
        html_report = format_html_report(report)

        # 출력
        print(markdown_report)
        print(f"\n{'='*60}\n")

        # 파일 저장
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(markdown_report)

            print(f"✅ 파일 저장: {output_path}")

        # DB 저장
        if args.save_db:
            report_id = save_report_to_db(args.account_id, report, markdown_report)
            print(f"✅ DB 저장 완료: report_id={report_id}")

        # n8n 전송 (HTML 형식)
        if args.send_n8n:
            report_type_name = "주간 성과 보고서" if args.type == "weekly" else "일일 성과 보고서"
            send_report_to_n8n(
                html_report,
                subject=report_type_name,
                recipient_email=os.getenv("REPORT_EMAIL_RECIPIENT")
            )

        print(f"\n{'='*60}")
        print("✅ 보고서 생성 완료")
        print(f"{'='*60}\n")

    except Exception as e:
        print(f"❌ 오류: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
