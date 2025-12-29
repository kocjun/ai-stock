"""
Paper Trading 실시간 모니터링 대시보드

Dash (Plotly) 기반 웹 대시보드
"""

import sys
from pathlib import Path
from datetime import datetime
import math
from typing import Optional

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import plotly.express as px
import pandas as pd

# 같은 디렉토리의 모듈들 import
sys.path.insert(0, str(Path(__file__).parent))

import dashboard_data as dd
import paper_trading as pt

# Dash 앱 초기화
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.FONT_AWESOME],
    title="Paper Trading Dashboard"
)

# 전역 설정
ACCOUNT_ID = 1
REFRESH_INTERVAL = 30000  # 30초 (밀리초 단위)
DEFAULT_RANGE_DAYS = 30
BENCHMARK_CHOICES = [
    {"label": "KOSPI", "value": "KS11"},
    {"label": "KOSDAQ", "value": "KQ11"}
]
BENCHMARK_LABELS = {item["value"]: item["label"] for item in BENCHMARK_CHOICES}
DEFAULT_BENCHMARK = BENCHMARK_CHOICES[0]["value"]


# ===== 유틸리티 함수 =====

def format_currency(value: float) -> str:
    """통화 포맷팅"""
    if value >= 0:
        return f"₩{value:,.0f}"
    else:
        return f"-₩{abs(value):,.0f}"


def format_percent(value: float) -> str:
    """퍼센트 포맷팅"""
    if value >= 0:
        return f"+{value:.2f}%"
    else:
        return f"{value:.2f}%"


def get_color_by_value(value: float) -> str:
    """값에 따른 색상 반환"""
    if value > 0:
        return "success"
    elif value < 0:
        return "danger"
    else:
        return "secondary"


# ===== 레이아웃 컴포넌트 =====

def create_header():
    """헤더 생성"""
    return html.Div([
        html.Div([
            html.Div("AQ", className="branding-icon"),
            html.Div([
                html.P("AstraQuant", className="meta-text mb-1"),
                html.H1("Paper Trading Dashboard", className="mb-0")
            ])
        ], className="branding"),
        html.Div([
            html.Span("마지막 업데이트", className="meta-text"),
            html.Span(id="last-update-time", className="meta-text")
        ], className="header-actions")
    ], className="dashboard-header")


def create_filter_bar():
    """글로벌 필터 바"""
    return html.Div([
        html.Div([
            html.Div([
                html.Label("조회 기간"),
                dcc.Dropdown(
                    id="performance-range",
                    options=[
                        {"label": "최근 30일", "value": 30},
                        {"label": "최근 90일", "value": 90},
                        {"label": "최근 180일", "value": 180}
                    ],
                    value=DEFAULT_RANGE_DAYS,
                    clearable=False,
                    className="control"
                )
            ], className="filter-group"),
            html.Div([
                html.Label("벤치마크"),
                dcc.Dropdown(
                    id="benchmark-select",
                    options=BENCHMARK_CHOICES,
                    value=DEFAULT_BENCHMARK,
                    clearable=False,
                    className="control"
                )
            ], className="filter-group")
        ], className="filter-grid"),
        html.Div([
            html.Button([
                html.I(className="fas fa-sync-alt"),
                "수동 업데이트"
            ], id="refresh-button", className="btn btn-primary btn-md")
        ], className="filter-actions")
    ], className="filter-bar")


def create_metric_card(title: str, value: str, subtitle: str = "", color: str = "primary"):
    """메트릭 카드 생성"""
    value_classes = ["kpi-value"]
    if color == "success":
        value_classes.append("text-positive")
    elif color == "danger":
        value_classes.append("text-negative")
    elif color not in ("primary", "info", "warning"):
        value_classes.append(color)

    subtitle_node = html.Div(subtitle, className="kpi-meta") if subtitle else None

    return html.Div([
        html.Div(title, className="kpi-label"),
        html.Div(value, className=" ".join(value_classes)),
        subtitle_node
    ], className="kpi-card")


def build_section(title: str, body, actions=None, section_id: Optional[str] = None):
    """섹션 공통 레이아웃"""
    header_children = [
        html.H4(title, className="section-title")
    ]
    if actions:
        header_children.append(html.Div(actions, className="section-actions"))

    return html.Div([
        html.Div(header_children, className="section-header"),
        html.Div(body, className="section-card")
    ], className="section", id=section_id)


def create_portfolio_section():
    """포트폴리오 현황 섹션"""
    body = html.Div([
        html.Div(id="account-metrics", className="kpi-stack"),
        html.Div([
            html.Div([
                html.H6("보유 종목", className="mb-3"),
                html.Div(id="portfolio-table", className="table-dense")
            ]),
            html.Div(dcc.Graph(id="portfolio-pie-chart", config={'displayModeBar': False}))
        ], className="portfolio-grid")
    ])
    return build_section("포트폴리오 현황", body, section_id="portfolio-section")


def create_performance_section():
    """성과 분석 섹션"""
    body = html.Div([
        html.Div(id="performance-metrics", className="kpi-grid"),
        html.Div(id="performance-insights", className="kpi-grid"),
        html.Div([
            dcc.Graph(id="value-history-chart"),
            dcc.Graph(id="daily-returns-chart")
        ], className="chart-grid"),
        html.Div(dcc.Graph(id="monthly-returns-chart"))
    ])
    return build_section("성과 분석", body, section_id="performance-section")


def create_trades_section():
    """거래 내역 섹션"""
    controls = html.Div([
        html.Div([
            html.Label("거래 유형"),
            dbc.RadioItems(
                id="trade-type-filter",
                options=[
                    {"label": "전체", "value": "all"},
                    {"label": "매수", "value": "buy"},
                    {"label": "매도", "value": "sell"}
                ],
                value="all",
                inline=True,
                className="chip-group"
            )
        ], className="filter-group"),
        html.Div([
            html.Label("조회 건수"),
            dcc.Input(
                id="trade-limit-input",
                type="number",
                value=20,
                min=5,
                max=100,
                step=5,
                placeholder="20",
                className="control"
            )
        ], className="filter-group")
    ], className="filter-grid")

    body = html.Div([
        controls,
        html.Div(id="trades-table", className="table-dense")
    ])
    return build_section("최근 거래 내역", body, section_id="trades-section")


# ===== 메인 레이아웃 =====

# app.layout은 모든 함수 정의 이후에 설정


# ===== 콜백 함수 =====

@app.callback(
    [
        Output("account-metrics", "children"),
        Output("portfolio-table", "children"),
        Output("portfolio-pie-chart", "figure"),
        Output("performance-metrics", "children"),
        Output("performance-insights", "children"),
        Output("value-history-chart", "figure"),
        Output("daily-returns-chart", "figure"),
        Output("monthly-returns-chart", "figure"),
        Output("last-update-time", "children")
    ],
    [
        Input("interval-component", "n_intervals"),
        Input("refresh-button", "n_clicks"),
        Input("performance-range", "value"),
        Input("benchmark-select", "value")
    ]
)
def update_dashboard(n_intervals, n_clicks, range_days, benchmark_code):
    """대시보드 전체 업데이트"""
    range_days = range_days or DEFAULT_RANGE_DAYS
    benchmark_code = benchmark_code or DEFAULT_BENCHMARK

    # 1. 계좌 요약 정보
    summary = dd.get_account_summary(ACCOUNT_ID)

    # 수동 새로고침 버튼으로만 포트폴리오 시세 갱신
    ctx = dash.callback_context
    if ctx.triggered and ctx.triggered[0]['prop_id'].split('.')[0] == 'refresh-button':
        try:
            pt.update_portfolio_values(ACCOUNT_ID)
            summary = dd.get_account_summary(ACCOUNT_ID)
        except Exception as e:
            print(f"포트폴리오 업데이트 실패: {e}")

    metrics = dd.get_performance_metrics(ACCOUNT_ID)

    cash_ratio = (summary['cash_balance'] / summary['total_value'] * 100) if summary['total_value'] else 0.0

    account_cards = [
        create_metric_card(
            "총 자산",
            format_currency(summary['total_value']),
            f"초기 자금: {format_currency(summary['initial_balance'])}",
            "primary"
        ),
        create_metric_card(
            "현금 잔고",
            format_currency(summary['cash_balance']),
            f"비중: {cash_ratio:.1f}%",
            "info"
        ),
        create_metric_card(
            "주식 평가액",
            format_currency(summary['stock_value']),
            f"보유 종목: {summary['num_positions']}개",
            "warning"
        ),
        create_metric_card(
            "총 수익",
            format_currency(summary['total_return']),
            format_percent(summary['return_pct']),
            get_color_by_value(summary['total_return'])
        )
    ]

    pnl_cards = [
        create_metric_card(
            "실현 손익",
            format_currency(metrics['realized_profit']),
            "누적 기준",
            get_color_by_value(metrics['realized_profit'])
        ),
        create_metric_card(
            "미실현 손익",
            format_currency(metrics['unrealized_profit']),
            "현재 포지션 기준",
            get_color_by_value(metrics['unrealized_profit'])
        ),
        create_metric_card(
            "평균 거래당 수익",
            format_currency(metrics['avg_profit_per_trade']),
            "실현 손익 / 총 거래 수",
            get_color_by_value(metrics['avg_profit_per_trade'])
        )
    ]

    account_metrics = html.Div([
        html.Div(account_cards, className="kpi-grid"),
        html.Div(pnl_cards, className="kpi-grid")
    ], className="kpi-stack")

    # 2. 포트폴리오 포지션
    positions_df = dd.get_portfolio_positions(ACCOUNT_ID)
    avg_holding_days = 0

    if len(positions_df) > 0:
        if 'first_buy_date' not in positions_df.columns:
            positions_df['first_buy_date'] = pd.NaT
        if 'sector' not in positions_df.columns:
            positions_df['sector'] = "-"

        positions_df['profit_loss'] = positions_df['profit_loss'].fillna(0.0)
        positions_df['first_buy_date'] = pd.to_datetime(positions_df['first_buy_date'], errors='coerce')
        positions_df['holding_days'] = (datetime.now() - positions_df['first_buy_date']).dt.days
        positions_df['holding_days'] = positions_df['holding_days'].fillna(0).astype(int)

        avg_holding_days_series = positions_df['holding_days'].replace(0, pd.NA)
        if avg_holding_days_series.notna().any():
            avg_holding_days = int(round(avg_holding_days_series.dropna().mean()))

        display_df = pd.DataFrame({
            '종목명': positions_df['name'],
            '섹터': positions_df.get('sector', '-'),
            '수량': positions_df['quantity'].apply(lambda x: f"{int(x):,}"),
            '평균 매입가': positions_df['avg_price'].apply(lambda x: f"{x:,.0f}"),
            '현재가': positions_df['current_price'].apply(lambda x: f"{x:,.0f}" if pd.notnull(x) else "-"),
            '평가액': positions_df['current_value'].apply(lambda x: f"{x:,.0f}"),
            '평가손익': positions_df['profit_loss'].apply(lambda x: f"{x:+,.0f}"),
            '손익률(%)': positions_df['profit_loss_pct'].apply(lambda x: f"{x:+.2f}%"),
            '보유일수': positions_df['holding_days'].apply(lambda x: f"{x}일" if x else "-"),
            '첫 매수일': positions_df['first_buy_date'].dt.strftime('%Y-%m-%d')
        })
        display_df = display_df.fillna("-")

        portfolio_table = dbc.Table.from_dataframe(
            display_df,
            striped=True,
            bordered=True,
            hover=True,
            responsive=True,
            size='sm',
            className="table table-dense"
        )

        # 파이 차트 (포트폴리오 비중)
        pie_fig = px.pie(
            positions_df,
            values='current_value',
            names='name',
            title='포트폴리오 비중',
            hole=0.4
        )
        pie_fig.update_layout(
            margin=dict(t=40, b=0, l=0, r=0),
            height=300
        )
    else:
        portfolio_table = html.P("보유 종목이 없습니다.", className="text-muted")
        pie_fig = go.Figure()
        pie_fig.add_annotation(
            text="보유 종목 없음",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="gray")
        )
        pie_fig.update_layout(
            margin=dict(t=40, b=0, l=0, r=0),
            height=300
        )

    # 3. 성과 지표
    performance_metrics = html.Div([
        create_metric_card(
            "총 거래 횟수",
            f"{metrics['total_trades']}건",
            f"매수 {metrics['buy_trades']} / 매도 {metrics['sell_trades']}",
            "primary"
        ),
        create_metric_card(
            "승률",
            f"{metrics['win_rate']:.1f}%",
            "익절 거래 비율",
            get_color_by_value(metrics['win_rate'] - 50)
        ),
        create_metric_card(
            "Sharpe Ratio",
            f"{metrics['sharpe_ratio']:.2f}",
            "위험 대비 수익",
            "info"
        ),
        create_metric_card(
            "최대 낙폭 (MDD)",
            f"{metrics['max_drawdown']:.2f}%",
            "최대 손실 구간",
            "danger"
        )
    ], className="kpi-grid")

    # 4. 추가 성과 인사이트
    daily_stats = dd.get_daily_performance_stats(ACCOUNT_ID, days=range_days)
    best_return = daily_stats.get('best_return', 0.0)
    worst_return = daily_stats.get('worst_return', 0.0)
    avg_daily_return = daily_stats.get('average_return', 0.0)

    insights_content = html.Div([
        create_metric_card(
            "최고 일간 수익률",
            format_percent(best_return),
            daily_stats.get('best_date', "-"),
            get_color_by_value(best_return)
        ),
        create_metric_card(
            "최저 일간 수익률",
            format_percent(worst_return),
            daily_stats.get('worst_date', "-"),
            get_color_by_value(worst_return)
        ),
        create_metric_card(
            "평균 일간 수익률",
            format_percent(avg_daily_return),
            f"최근 {range_days}일 기준",
            get_color_by_value(avg_daily_return)
        ),
        create_metric_card(
            "평균 보유 일수",
            f"{avg_holding_days}일",
            "현재 포지션 기준",
            "secondary"
        )
    ], className="kpi-grid")

    # 4. 자산 추이 차트
    history_df = dd.get_portfolio_history(ACCOUNT_ID, days=range_days)
    benchmark_label = BENCHMARK_LABELS.get(benchmark_code, benchmark_code)
    benchmark_df = dd.get_benchmark_history(benchmark_code, days=range_days)

    if len(history_df) > 0:
        value_fig = go.Figure()
        value_fig.add_trace(go.Scatter(
            x=history_df['snapshot_date'],
            y=history_df['total_value'],
            mode='lines+markers',
            name='총 자산',
            line=dict(color='#0d6efd', width=2),
            fill='tozeroy'
        ))
        if len(benchmark_df) > 0 and not history_df.empty:
            base_value = history_df['total_value'].iloc[0]
            scaled_benchmark = benchmark_df.copy()
            scaled_benchmark['scaled_close'] = (
                scaled_benchmark['close'] / scaled_benchmark['close'].iloc[0] * base_value
            )
            value_fig.add_trace(go.Scatter(
                x=scaled_benchmark['date'],
                y=scaled_benchmark['scaled_close'],
                mode='lines',
                name=f"{benchmark_label} (벤치마크)",
                line=dict(color='#6c757d', dash='dash')
            ))

        value_fig.update_layout(
            title=f'자산 추이 (최근 {range_days}일)',
            xaxis_title='날짜',
            yaxis_title='총 자산 (원)',
            hovermode='x unified',
            margin=dict(t=40, b=40, l=60, r=20)
        )
    else:
        value_fig = go.Figure()
        value_fig.add_annotation(
            text="데이터가 충분하지 않습니다.",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="gray")
        )
        value_fig.update_layout(
            title=f'자산 추이 (최근 {range_days}일)',
            margin=dict(t=40, b=40, l=60, r=20)
        )

    # 5. 일별 수익률 차트
    returns_df = dd.get_daily_returns(ACCOUNT_ID, days=range_days)

    if len(returns_df) > 0:
        colors = ['green' if x >= 0 else 'red' for x in returns_df['daily_return']]
        returns_fig = go.Figure()
        returns_fig.add_trace(go.Bar(
            x=returns_df['date'],
            y=returns_df['daily_return'],
            marker_color=colors,
            name='일별 수익률'
        ))
        returns_fig.update_layout(
            title=f'일별 수익률 (최근 {range_days}일)',
            xaxis_title='날짜',
            yaxis_title='수익률 (%)',
            margin=dict(t=40, b=40, l=60, r=20),
            height=300
        )
    else:
        returns_fig = go.Figure()
        returns_fig.add_annotation(
            text="데이터 없음",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=14, color="gray")
        )
        returns_fig.update_layout(
            title=f'일별 수익률 (최근 {range_days}일)',
            margin=dict(t=40, b=40, l=60, r=20),
            height=300
        )

    # 6. 월간 수익률
    months = max(3, math.ceil(range_days / 30))
    monthly_df = dd.get_monthly_returns(ACCOUNT_ID, months=months)
    benchmark_monthly_df = dd.get_benchmark_monthly_returns(benchmark_code, months=months)

    monthly_fig = go.Figure()

    if len(monthly_df) > 0:
        monthly_colors = ['#198754' if x >= 0 else '#dc3545' for x in monthly_df['return_pct']]
        monthly_fig.add_trace(go.Bar(
            x=monthly_df['period'],
            y=monthly_df['return_pct'],
            marker_color=monthly_colors,
            name='포트폴리오'
        ))

    if len(benchmark_monthly_df) > 0:
        benchmark_colors = ['#0dcaf0' if x >= 0 else '#6c757d' for x in benchmark_monthly_df['return_pct']]
        monthly_fig.add_trace(go.Bar(
            x=benchmark_monthly_df['period'],
            y=benchmark_monthly_df['return_pct'],
            marker_color=benchmark_colors,
            name=benchmark_label
        ))

    if len(monthly_fig.data) > 0:
        monthly_fig.update_layout(
            title=f'월간 수익률 (최근 {months}개월)',
            xaxis_title='월',
            yaxis_title='수익률 (%)',
            margin=dict(t=40, b=40, l=60, r=20),
            height=320,
            barmode='group'
        )
    else:
        monthly_fig.add_annotation(
            text="월간 수익률 데이터가 충분하지 않습니다.",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=14, color="gray")
        )
        monthly_fig.update_layout(
            title=f'월간 수익률 (최근 {months}개월)',
            margin=dict(t=40, b=40, l=60, r=20),
            height=320
        )

    # 7. 마지막 업데이트 시간
    last_update = dd.get_last_update_time(ACCOUNT_ID)
    if last_update:
        update_time_text = f"마지막 업데이트: {last_update.strftime('%Y-%m-%d %H:%M:%S')}"
    else:
        update_time_text = "마지막 업데이트: -"

    return (
        account_metrics,
        portfolio_table,
        pie_fig,
        performance_metrics,
        insights_content,
        value_fig,
        returns_fig,
        monthly_fig,
        update_time_text
    )


@app.callback(
    Output("trades-table", "children"),
    [
        Input("trade-type-filter", "value"),
        Input("trade-limit-input", "value"),
        Input("interval-component", "n_intervals"),
        Input("refresh-button", "n_clicks")
    ]
)
def update_trades_table(trade_type, limit, n_intervals, n_clicks):
    """거래 내역 테이블 업데이트"""

    if limit is None or limit < 1:
        limit = 20

    # 거래 내역 조회
    trade_type_filter = None if trade_type == "all" else trade_type
    trades_df = dd.get_recent_trades(
        ACCOUNT_ID,
        limit=limit,
        trade_type=trade_type_filter
    )

    if len(trades_df) > 0:
        # 거래 유형 한글화
        trades_df['trade_type'] = trades_df['trade_type'].map({
            'buy': '매수',
            'sell': '매도'
        })

        # 날짜 포맷팅
        trades_df['trade_date'] = trades_df['trade_date'].dt.strftime('%Y-%m-%d %H:%M')

        trades_table = dbc.Table.from_dataframe(
            trades_df[[
                'trade_date', 'name', 'trade_type', 'quantity',
                'price', 'total_amount', 'reason'
            ]].rename(columns={
                'trade_date': '거래 일시',
                'name': '종목명',
                'trade_type': '유형',
                'quantity': '수량',
                'price': '가격',
                'total_amount': '거래 금액',
                'reason': '사유'
            }),
            striped=True,
            bordered=True,
            hover=True,
            responsive=True,
            size='sm',
            className="table table-dense"
        )

        return trades_table
    else:
        return html.P("거래 내역이 없습니다.", className="text-muted")


# ===== AI 인사이트 섹션 함수 =====

def create_ai_insights_section():
    """AI 분석 인사이트 섹션"""
    body = html.Div([
        html.Div([
            html.Div([
                html.H6("포트폴리오 AI 전망", className="mb-3"),
                html.Div(id="portfolio-ai-summary")
            ]),
            html.Div([
                html.H6("섹터별 배분 & AI 점수", className="mb-3"),
                dcc.Graph(id="sector-allocation-chart", config={'displayModeBar': False})
            ])
        ], className="portfolio-grid"),
        html.Div([
            html.H6("보유 종목 AI 분석", className="mb-3"),
            html.Div(id="holding-ai-analysis-table")
        ], className="table-dense")
    ])
    return build_section("AI 분석 인사이트", body, section_id="ai-insights")


def create_stock_detail_modal():
    """종목 상세 분석 정보 모달"""
    return dbc.Modal([
        dbc.ModalHeader([
            html.Span(id="modal-stock-name", className="text-primary"),
            html.Span(" 상세 분석", className="ms-2")
        ]),
        dbc.ModalBody([
            dbc.Row([
                dbc.Col([
                    html.H6("종합 평가", className="text-muted mb-3"),
                    dbc.Row([
                        dbc.Col([
                            html.Div([
                                html.Div(id="modal-overall-score", className="h3 text-primary mb-2"),
                                html.Small("종합 점수", className="text-muted")
                            ], className="text-center")
                        ], xs=4),
                        dbc.Col([
                            html.Div([
                                html.Div(id="modal-confidence-level", className="h3 text-success mb-2"),
                                html.Small("신뢰도", className="text-muted")
                            ], className="text-center")
                        ], xs=4),
                        dbc.Col([
                            html.Div([
                                html.Div(id="modal-risk-grade", className="h3 mb-2"),
                                html.Small("리스크 등급", className="text-muted")
                            ], className="text-center")
                        ], xs=4)
                    ])
                ], md=12, lg=5),
                dbc.Col([
                    html.H6("세부 점수", className="text-muted mb-3"),
                    html.Div([
                        html.Div([
                            html.Small("재무 점수", className="text-muted d-block mb-1"),
                            dbc.Progress(id="modal-financial-score", color="success", className="mb-3")
                        ]),
                        html.Div([
                            html.Small("기술적 점수", className="text-muted d-block mb-1"),
                            dbc.Progress(id="modal-technical-score", color="info", className="mb-3")
                        ]),
                        html.Div([
                            html.Small("리스크 점수", className="text-muted d-block mb-1"),
                            dbc.Progress(id="modal-risk-score", color="warning", className="mb-3")
                        ])
                    ])
                ], md=12, lg=7)
            ]),
            html.Hr(),
            dbc.Row([
                dbc.Col([
                    html.H6("가격 예측", className="text-muted mb-2"),
                    html.Div([
                        html.Span("목표가: ", className="fw-bold"),
                        html.Span(id="modal-target-price")
                    ]),
                    html.Div([
                        html.Span("기대 수익률: ", className="fw-bold"),
                        html.Span(id="modal-expected-return")
                    ])
                ], md=12, lg=6),
                dbc.Col([
                    html.H6("리스크 지표", className="text-muted mb-2"),
                    html.Div([
                        html.Span("변동성: ", className="fw-bold"),
                        html.Span(id="modal-volatility")
                    ]),
                    html.Div([
                        html.Span("최대 낙폭: ", className="fw-bold"),
                        html.Span(id="modal-max-drawdown")
                    ])
                ], md=12, lg=6)
            ]),
            html.Hr(),
            html.H6("매수 근거", className="text-muted mb-2"),
            html.Div(id="modal-buy-rationale", className="alert alert-info")
        ]),
        dbc.ModalFooter([
            dbc.Button("닫기", id="close-modal", className="ms-auto")
        ])
    ], id="stock-detail-modal", size="lg", centered=True)


@app.callback(
    [Output("portfolio-ai-summary", "children"),
     Output("sector-allocation-chart", "figure"),
     Output("holding-ai-analysis-table", "children")],
    [Input("refresh-interval", "n_intervals")],
    prevent_initial_call=False
)
def update_ai_insights(n_intervals):
    """AI 인사이트 업데이트"""
    try:
        # 포트폴리오 AI 요약 조회
        portfolio_summary = dd.get_portfolio_ai_summary(ACCOUNT_ID)

        if portfolio_summary:
            summary_content = dbc.Row([
                dbc.Col([
                    html.Div([
                        html.H6("시장 전망", className="text-muted"),
                        html.Div(
                            html.Badge(
                                portfolio_summary.get('market_sentiment', 'Neutral'),
                                color="success" if portfolio_summary.get('market_sentiment') == 'Bullish'
                                else "warning" if portfolio_summary.get('market_sentiment') == 'Neutral'
                                else "danger",
                                className="p-2"
                            ),
                            className="mb-3"
                        ),
                        html.Small(portfolio_summary.get('market_analysis', 'N/A')[:200], className="text-muted")
                    ])
                ], xs=6),
                dbc.Col([
                    html.Div([
                        html.H6("포트폴리오 지표", className="text-muted"),
                        html.Div([
                            html.Div([
                                html.Small("기대 수익률", className="text-muted"),
                                html.Div(
                                    f"{portfolio_summary.get('expected_return', 0):.2f}%",
                                    className="h5 text-success"
                                )
                            ]),
                            html.Div([
                                html.Small("기대 변동성", className="text-muted"),
                                html.Div(
                                    f"{portfolio_summary.get('expected_volatility', 0):.2f}%",
                                    className="h5 text-warning"
                                )
                            ])
                        ])
                    ])
                ], xs=6)
            ])
        else:
            summary_content = dbc.Alert("AI 포트폴리오 인사이트 데이터가 없습니다", color="warning")

        # 섹터 배분 차트
        sector_data = dd.get_sector_allocation_analysis(ACCOUNT_ID)

        if sector_data:
            sectors = list(sector_data.keys())
            weights = [sector_data[s]['weight'] for s in sectors]

            fig_sector = go.Figure(data=[
                go.Pie(
                    labels=sectors,
                    values=weights,
                    textposition='inside',
                    textinfo='label+percent'
                )
            ])
            fig_sector.update_layout(height=300, margin=dict(l=0, r=0, t=0, b=0))
        else:
            fig_sector = go.Figure()
            fig_sector.add_annotation(text="섹터 데이터 없음", showarrow=False)
            fig_sector.update_layout(height=300)

        # 보유 종목 AI 분석 테이블
        holding_analysis = dd.get_holding_ai_analysis(ACCOUNT_ID)

        if holding_analysis:
            table_rows = []
            for analysis in holding_analysis:
                table_rows.append(
                    html.Tr([
                        html.Td(html.Strong(analysis.get('code', 'N/A'))),
                        html.Td(f"{analysis.get('quantity', 0):.0f}주"),
                        html.Td(
                            html.Span(
                                f"{analysis.get('overall_score', 0):.1f}",
                                className="badge bg-success" if analysis.get('overall_score', 0) >= 70
                                else "badge bg-warning"
                            )
                        ),
                        html.Td(
                            html.Span(
                                f"₩{analysis.get('target_price', 0):,.0f}",
                                className="text-primary"
                            )
                        ),
                        html.Td(
                            html.Span(
                                analysis.get('risk_grade', 'N/A'),
                                className="badge bg-danger" if analysis.get('risk_grade') == 'High'
                                else "badge bg-warning" if analysis.get('risk_grade') == 'Medium'
                                else "badge bg-success"
                            )
                        ),
                        html.Td(
                            html.Button(
                                "상세보기",
                                id={"type": "detail-btn", "index": analysis.get('code')},
                                className="btn btn-sm btn-outline-primary",
                                n_clicks=0
                            )
                        )
                    ])
                )

            table_content = dbc.Table(
                [
                    html.Thead(
                        html.Tr([
                            html.Th("종목"),
                            html.Th("수량"),
                            html.Th("AI 점수"),
                            html.Th("목표가"),
                            html.Th("리스크"),
                            html.Th("")
                        ])
                    ),
                    html.Tbody(table_rows)
                ],
                striped=True,
                bordered=True,
                hover=True,
                responsive=True,
                size="sm",
                className="table table-dense"
            )
        else:
            table_content = dbc.Alert("AI 분석 데이터가 없습니다", color="warning")

        return summary_content, fig_sector, table_content

    except Exception as e:
        print(f"AI 인사이트 업데이트 실패: {e}")
        return dbc.Alert(f"오류: {str(e)[:100]}", color="danger"), go.Figure(), html.Div()


# ===== 앱 레이아웃 설정 (모든 함수 정의 이후) =====

app.layout = html.Div([
    html.Div([
        create_header(),
        create_filter_bar(),

        dcc.Interval(
            id='refresh-interval',
            interval=REFRESH_INTERVAL,
            n_intervals=0
        ),
        dcc.Interval(
            id='interval-component',
            interval=REFRESH_INTERVAL,
            n_intervals=0
        ),

        html.Div([
            html.Div([
                create_portfolio_section(),
                create_trades_section()
            ]),
            html.Div([
                create_performance_section(),
                create_ai_insights_section()
            ])
        ], className="content-grid"),

        create_stock_detail_modal()
    ], className="app-container")
], className="app-shell")


# ===== 메인 실행 =====

if __name__ == "__main__":
    print("=" * 60)
    print("📊 Paper Trading Dashboard")
    print("=" * 60)
    print(f"서버 시작 중...")
    print(f"접속 주소: http://localhost:8050")
    print(f"계정 ID: {ACCOUNT_ID}")
    print(f"자동 새로고침: {REFRESH_INTERVAL/1000}초마다")
    print("=" * 60)

    app.run(debug=True, host='0.0.0.0', port=8050)
