"""
제외 종목 관리 유틸리티
- 포트폴리오에서 제외할 종목 관리
- 데이터베이스 기반 제외 목록
"""
import os
import psycopg2
from typing import List, Dict, Optional
from datetime import datetime


def get_db_connection():
    """PostgreSQL 연결 생성"""
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        database=os.getenv("DB_NAME", "investment_db"),
        user=os.getenv("DB_USER", "invest_user"),
        password=os.getenv("DB_PASSWORD", "invest_pass_2024!")
    )


def add_excluded_stock(code: str, reason: str, excluded_by: str = "user", notes: Optional[str] = None) -> bool:
    """
    제외 종목 추가

    Args:
        code: 종목코드
        reason: 제외 사유
        excluded_by: 제외 주체 (기본값: user)
        notes: 추가 메모

    Returns:
        성공 여부
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # add_excluded_stock 함수 호출
        cur.execute(
            "SELECT add_excluded_stock(%s, %s, %s, %s)",
            (code, reason, excluded_by, notes)
        )
        exclusion_id = cur.fetchone()[0]

        conn.commit()
        cur.close()
        conn.close()

        print(f"✅ 제외 종목 추가: {code} (ID: {exclusion_id})")
        return True

    except Exception as e:
        print(f"❌ 제외 종목 추가 실패: {e}")
        return False


def remove_excluded_stock(code: str) -> bool:
    """
    제외 종목 해제

    Args:
        code: 종목코드

    Returns:
        성공 여부
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # remove_excluded_stock 함수 호출
        cur.execute("SELECT remove_excluded_stock(%s)", (code,))
        success = cur.fetchone()[0]

        conn.commit()
        cur.close()
        conn.close()

        if success:
            print(f"✅ 제외 종목 해제: {code}")
        else:
            print(f"⚠️  제외 종목이 아니거나 이미 해제됨: {code}")

        return success

    except Exception as e:
        print(f"❌ 제외 종목 해제 실패: {e}")
        return False


def is_stock_excluded(code: str) -> bool:
    """
    종목이 제외 목록에 있는지 확인

    Args:
        code: 종목코드

    Returns:
        제외 여부
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("SELECT is_stock_excluded(%s)", (code,))
        excluded = cur.fetchone()[0]

        cur.close()
        conn.close()

        return excluded

    except Exception as e:
        print(f"❌ 제외 종목 확인 실패: {e}")
        return False


def get_excluded_stocks() -> List[Dict]:
    """
    모든 제외 종목 조회

    Returns:
        제외 종목 리스트
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT
                exclusion_id,
                code,
                stock_name,
                sector,
                market_type,
                reason,
                excluded_by,
                excluded_at,
                notes
            FROM v_excluded_stocks
            ORDER BY excluded_at DESC
        """)

        columns = [desc[0] for desc in cur.description]
        rows = cur.fetchall()

        excluded_stocks = []
        for row in rows:
            stock_dict = dict(zip(columns, row))
            # datetime을 문자열로 변환
            if stock_dict.get('excluded_at'):
                stock_dict['excluded_at'] = stock_dict['excluded_at'].isoformat()
            excluded_stocks.append(stock_dict)

        cur.close()
        conn.close()

        return excluded_stocks

    except Exception as e:
        print(f"❌ 제외 종목 조회 실패: {e}")
        return []


def filter_excluded_stocks(stock_codes: List[str]) -> List[str]:
    """
    종목 리스트에서 제외 종목 필터링

    Args:
        stock_codes: 종목코드 리스트

    Returns:
        제외 종목이 제거된 종목코드 리스트
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # PostgreSQL 배열로 변환하여 함수 호출
        cur.execute("SELECT filter_excluded_stocks(%s)", (stock_codes,))
        filtered_codes = cur.fetchone()[0]

        cur.close()
        conn.close()

        # 제외된 종목 출력
        excluded = set(stock_codes) - set(filtered_codes or [])
        if excluded:
            print(f"ℹ️  제외된 종목: {', '.join(excluded)}")

        return filtered_codes or []

    except Exception as e:
        print(f"❌ 종목 필터링 실패: {e}")
        # 실패 시 원본 반환
        return stock_codes


def filter_excluded_recommendations(recommendations: List[Dict]) -> List[Dict]:
    """
    AI 추천 결과에서 제외 종목 필터링

    Args:
        recommendations: AI 추천 종목 리스트 [{'code': '005930', 'weight': 0.3, ...}, ...]

    Returns:
        제외 종목이 제거된 추천 리스트
    """
    if not recommendations:
        return []

    # 종목코드 추출
    codes = [rec.get('code') for rec in recommendations if rec.get('code')]

    # 제외 종목 필터링
    filtered_codes = filter_excluded_stocks(codes)

    # 필터링된 종목만 반환
    filtered_recs = [rec for rec in recommendations if rec.get('code') in filtered_codes]

    # 비중 재조정 (합이 1이 되도록)
    if filtered_recs:
        total_weight = sum(rec.get('weight', 0) for rec in filtered_recs)
        if total_weight > 0:
            for rec in filtered_recs:
                rec['weight'] = rec.get('weight', 0) / total_weight

    return filtered_recs


def print_excluded_stocks():
    """제외 종목 목록 출력 (CLI용)"""
    excluded_stocks = get_excluded_stocks()

    if not excluded_stocks:
        print("제외된 종목이 없습니다.")
        return

    print(f"\n{'='*80}")
    print(f"제외 종목 목록 ({len(excluded_stocks)}개)")
    print(f"{'='*80}\n")

    for stock in excluded_stocks:
        code = stock.get('code', 'N/A')
        name = stock.get('stock_name', 'N/A')
        sector = stock.get('sector', 'N/A')
        reason = stock.get('reason', 'N/A')
        excluded_at = stock.get('excluded_at', 'N/A')
        excluded_by = stock.get('excluded_by', 'N/A')
        notes = stock.get('notes', '')

        print(f"[{code}] {name}")
        print(f"  섹터: {sector}")
        print(f"  사유: {reason}")
        print(f"  제외일: {excluded_at}")
        print(f"  제외자: {excluded_by}")
        if notes:
            print(f"  메모: {notes}")
        print()


if __name__ == "__main__":
    # 테스트용
    print("제외 종목 관리 유틸리티")
    print("\n현재 제외 종목:")
    print_excluded_stocks()
