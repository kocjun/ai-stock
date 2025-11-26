"""
시장 지표 스냅샷 유틸리티

FinanceDataReader를 이용해 KOSPI/KOSDAQ/환율 등 주요 수치를
요약 형태로 반환한다.
"""

from __future__ import annotations

import os
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional
from urllib.parse import quote_plus

import requests

try:
    import FinanceDataReader as fdr
except ImportError:  # pragma: no cover - 러ntime 설치 안 된 경우 대비
    fdr = None


YAHOO_SYMBOL_MAP = {
    "KS11": "^KS11",
    "KQ11": "^KQ11",
    "USD/KRW": "KRW=X",
}


def _fetch_symbol(symbol: str, lookback_days: int = 7) -> Optional[Dict]:
    """심볼별 종가/변동률 계산"""
    data = _fetch_from_fdr(symbol, lookback_days)
    if data is not None:
        return data
    return _fetch_from_yahoo(symbol)


def _fetch_from_fdr(symbol: str, lookback_days: int) -> Optional[Dict]:
    if fdr is None:
        return None

    end = datetime.now()
    start = end - timedelta(days=lookback_days)

    try:
        df = fdr.DataReader(symbol, start, end)
    except Exception as exc:
        print(f"[MarketMetrics] Yahoo fetch failed for {symbol}: {exc}")
        return None

    if df is None or df.empty:
        return None

    df = df.dropna(subset=["Close"])
    if df.empty:
        return None

    latest = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else latest

    close = float(latest["Close"])
    change = close - float(prev["Close"])
    pct = (change / float(prev["Close"])) * 100 if float(prev["Close"]) != 0 else 0.0

    return {
        "close": close,
        "change": change,
        "pct": pct,
        "date": latest.name.strftime("%Y-%m-%d"),
    }


def _fetch_from_yahoo(symbol: str) -> Optional[Dict]:
    mapped_symbol = YAHOO_SYMBOL_MAP.get(symbol, symbol)
    url = f"https://query2.finance.yahoo.com/v8/finance/chart/{quote_plus(mapped_symbol)}"
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/118.0 Safari/537.36"
    }
    params = {"range": "5d", "interval": "1d"}

    try:
        if os.getenv("MARKET_METRICS_DEBUG"):
            print(f"[MarketMetrics] fetching {symbol} from Yahoo chart API")
        resp = requests.get(url, params=params, headers=headers, timeout=8)
        if resp.status_code == 429:
            time.sleep(1.2)
            resp = requests.get(url, params=params, headers=headers, timeout=8)
        resp.raise_for_status()
        payload = resp.json()
        if os.getenv("MARKET_METRICS_DEBUG"):
            print(f"[MarketMetrics] env flag check for {symbol}: {os.getenv('MARKET_METRICS_DEBUG')}")
            print(f"[MarketMetrics] raw payload for {symbol}: {list(payload.keys())}")
        chart_result = payload.get("chart", {}).get("result", [])
        if not chart_result:
            if os.getenv("MARKET_METRICS_DEBUG"):
                print(f"[MarketMetrics] empty result for {symbol}: {payload.get('chart')}")
            return None

        result = chart_result[0]
        timestamps = result.get("timestamp", [])
        quote_data = result.get("indicators", {}).get("quote", [])
        if not timestamps or not quote_data:
            if os.getenv("MARKET_METRICS_DEBUG"):
                print(f"[MarketMetrics] quote missing for {symbol}")
            return None

        closes = quote_data[0].get("close", [])
        pairs = [
            (ts, close)
            for ts, close in zip(timestamps, closes)
            if close is not None
        ]
        if os.getenv("MARKET_METRICS_DEBUG"):
            print(f"[MarketMetrics] {symbol} pairs={len(pairs)}")
        if not pairs:
            if os.getenv("MARKET_METRICS_DEBUG"):
                print(f"[MarketMetrics] no valid closes for {symbol}: {closes}")
            return None

        latest_ts, latest_close = pairs[-1]
        prev_ts, prev_close = pairs[-2] if len(pairs) > 1 else pairs[-1]

        latest_dt = datetime.fromtimestamp(latest_ts, tz=timezone.utc)
        prev_close = float(prev_close) if prev_close is not None else float(latest_close)
        change = float(latest_close) - float(prev_close)
        pct = (change / prev_close) * 100 if prev_close else 0.0

        return {
            "close": float(latest_close),
            "change": change,
            "pct": pct,
            "date": latest_dt.strftime("%Y-%m-%d"),
        }

    except Exception as exc:
        if os.getenv("MARKET_METRICS_DEBUG"):
            print(f"[MarketMetrics] Yahoo fetch failed for {symbol}: {exc}")
        return None


def get_market_snapshot() -> Dict:
    """주요 지수를 포함한 요약 정보"""
    snapshot = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "kospi": _fetch_symbol("KS11"),
        "kosdaq": _fetch_symbol("KQ11"),
        "usdkrw": _fetch_symbol("USD/KRW"),
    }
    return snapshot


def format_snapshot_lines(snapshot: Dict) -> str:
    """마크다운 형태의 지표 요약 문자열"""
    def _format_line(label: str, data: Optional[Dict]) -> str:
        if not data:
            return f"- {label}: 데이터 없음"
        direction = "▲" if data["change"] > 0 else ("▼" if data["change"] < 0 else "―")
        return (
            f"- {label}: {data['close']:.2f} ({direction} {data['pct']:+.2f}%) "
            f"[{data['date']}]"
        )

    lines = [
        "## 📈 시장 지표 스냅샷",
        _format_line("KOSPI", snapshot.get("kospi")),
        _format_line("KOSDAQ", snapshot.get("kosdaq")),
        _format_line("USD/KRW", snapshot.get("usdkrw")),
        "",
    ]
    return "\n".join(lines)


__all__ = ["get_market_snapshot", "format_snapshot_lines"]
