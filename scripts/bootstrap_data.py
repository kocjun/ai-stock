#!/usr/bin/env python3
"""
데이터 파이프라인 초기 시딩 및 기본 가상 계좌 생성 스크립트.

용도:
    docker compose --env-file ../.env exec ai-stock-app \
        bash -lc "python scripts/bootstrap_data.py"
"""

from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

from core.utils.db_utils import get_db_connection


MIN_STOCKS = int(os.getenv("BOOTSTRAP_MIN_STOCKS", "30"))
MAX_PRICE_AGE_DAYS = int(os.getenv("BOOTSTRAP_MAX_PRICE_AGE", "5"))
DEFAULT_ACCOUNT_NAME = os.getenv("BOOTSTRAP_ACCOUNT_NAME", "AI Comprehensive")
DEFAULT_ACCOUNT_BALANCE = Decimal(os.getenv("BOOTSTRAP_ACCOUNT_BALANCE", "10000000"))


def run_data_curator() -> None:
    """investment_crew 실행을 통해 종목/가격 데이터를 수집."""
    print("[bootstrap] Running investment_crew.py to collect market data...")
    subprocess.run(
        [sys.executable, "core/agents/investment_crew.py"],
        check=True,
    )


def ensure_market_data() -> None:
    """stocks/prices 테이블 상태 확인 후 필요 시 수집."""
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM stocks;")
        stock_count = cur.fetchone()[0]

        cur.execute("SELECT MAX(date) FROM prices;")
        latest_price_date = cur.fetchone()[0]

        needs_collection = False
        if stock_count < MIN_STOCKS:
            print(
                f"[bootstrap] Stock count {stock_count} < {MIN_STOCKS}. "
                "Collecting data..."
            )
            needs_collection = True
        elif latest_price_date is None:
            print("[bootstrap] No price history found. Collecting data...")
            needs_collection = True
        else:
            age = datetime.utcnow().date() - latest_price_date
            if age > timedelta(days=MAX_PRICE_AGE_DAYS):
                print(
                    f"[bootstrap] Price data is {age.days} days old. "
                    "Refreshing..."
                )
                needs_collection = True

        if needs_collection:
            run_data_curator()
        else:
            print(
                f"[bootstrap] Market data looks healthy "
                f"(stocks={stock_count}, latest_price={latest_price_date})."
            )


def ensure_virtual_account() -> None:
    """기본 가상 계좌가 없으면 생성."""
    schema_path = Path("paper_trading/schema.sql")

    with get_db_connection() as conn:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute(schema_path.read_text(encoding="utf-8"))

        with conn.cursor() as cur:
            cur.execute("SELECT account_id FROM virtual_accounts LIMIT 1;")
            row = cur.fetchone()
            if row:
                print(f"[bootstrap] Existing virtual account found (ID={row[0]}).")
                return

        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO virtual_accounts (
                    account_name, initial_balance, current_balance, strategy
                ) VALUES (%s, %s, %s, %s)
                RETURNING account_id;
                """,
                (
                    DEFAULT_ACCOUNT_NAME,
                    DEFAULT_ACCOUNT_BALANCE,
                    DEFAULT_ACCOUNT_BALANCE,
                    "ai_comprehensive",
                ),
            )
            new_id = cur.fetchone()[0]
            conn.commit()
            print(
                f"[bootstrap] Created default virtual account "
                f"(ID={new_id}, balance={DEFAULT_ACCOUNT_BALANCE})."
            )


def main() -> None:
    print("=" * 80)
    print("데이터 파이프라인 부트스트랩")
    print("=" * 80)

    ensure_market_data()
    ensure_virtual_account()

    print("[bootstrap] Done.")


if __name__ == "__main__":
    main()
