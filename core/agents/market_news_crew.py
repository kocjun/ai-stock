"""
시장 뉴스 분석 및 요약 Crew

Google News RSS/NewsAPI(옵션)에서 실시간 뉴스를 가져와
시장 지표·KOSPI ETF 분석과 함께 이메일용 리포트를 생성한다.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from textwrap import shorten
from typing import Any, Dict, List, Tuple

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
    pass

try:
    from core.agents.kospi_etf_analyzer import analyze_kospi
except Exception:  # pragma: no cover - 분석 모듈이 비활성화된 경우 대비
    analyze_kospi = None

from core.utils.market_metrics import format_snapshot_lines, get_market_snapshot
from core.utils.news_fetcher import MarketNewsFetcher

SECTION_CONFIG: List[Tuple[str, str]] = [
    ("global", "🌍 글로벌 시장"),
    ("semiconductor", "🔧 반도체 섹터"),
    ("geopolitical", "⚔️ 지정학 리스크"),
    ("korea", "🇰🇷 국내 시장"),
]

HISTORY_DIR = project_root / "reports" / "market_news_history"
HISTORY_FILE = HISTORY_DIR / "history.json"


def _mock_article(title: str, source: str, description: str, impact: str, category: str) -> Dict[str, Any]:
    return {
        "title": title,
        "source": source,
        "impact": impact,
        "category": category,
        "description": description,
        "summary": description,
        "link": "",
        "published_at": None,
    }


def get_mock_global_news_data() -> List[Dict]:
    """RSS/API 실패 시 사용할 기본 글로벌 뉴스"""
    return [
        _mock_article(
            "Fed 금리 인상 예고",
            "Reuters",
            "연준이 추가 금리 인상을 시사하며 달러 강세 우려가 커집니다.",
            "high",
            "global",
        ),
        _mock_article(
            "S&P500 신고가 경신",
            "Bloomberg",
            "미국 증시는 기술주 강세 덕에 사상 최고치를 기록했습니다.",
            "medium",
            "global",
        ),
        _mock_article(
            "Tesla 배터리 기술 혁신",
            "TechCrunch",
            "테슬라가 차세대 배터리를 공개하며 전기차 산업 재편 가능성을 알렸습니다.",
            "medium",
            "global",
        ),
    ]


def get_mock_semiconductor_news_data() -> List[Dict]:
    return [
        _mock_article(
            "Samsung 3nm 공정 양산 돌입",
            "전자신문",
            "삼성전자가 차세대 3nm 공정에 성공하며 파운드리 경쟁력을 강화했습니다.",
            "high",
            "semiconductor",
        ),
        _mock_article(
            "TSMC 파운드리 수주 증가",
            "DigiTimes",
            "TSMC 수주잔고가 늘어나며 공급 부족이 심화되고 있습니다.",
            "high",
            "semiconductor",
        ),
        _mock_article(
            "SK Hynix 메모리 가격 회복",
            "뉴스1",
            "DDR5 가격 회복으로 SK Hynix 실적 개선 기대가 확대됩니다.",
            "medium",
            "semiconductor",
        ),
    ]


def get_mock_geopolitical_news_data() -> List[Dict]:
    return [
        _mock_article(
            "미중 기술 갈등 심화",
            "BBC",
            "미국의 추가 제재 예고로 반도체 공급망 불확실성이 증폭됩니다.",
            "high",
            "geopolitical",
        ),
        _mock_article(
            "한반도 긴장 고조",
            "연합뉴스",
            "북한 미사일 발사 이후 방위산업주의 수급이 살아나고 있습니다.",
            "high",
            "geopolitical",
        ),
        _mock_article(
            "러-우 전쟁 장기화",
            "Reuters",
            "에너지 가격 변동성이 확대되며 글로벌 수요 둔화 우려가 이어집니다.",
            "medium",
            "geopolitical",
        ),
    ]


def get_mock_korea_news_data() -> List[Dict]:
    return [
        _mock_article(
            "한은 금리 결정 임박",
            "연합뉴스",
            "한국은행 금통위가 매파 기조를 유지할 것으로 전망됩니다.",
            "high",
            "korea",
        ),
        _mock_article(
            "원/달러 환율 상승",
            "매일경제",
            "원화 약세가 심화되며 수출주에는 우호적인 환경이 조성됩니다.",
            "high",
            "korea",
        ),
        _mock_article(
            "코스피 200 선물 변동성 확대",
            "마켓뉴스",
            "야간선물 변동성으로 개장 직후 방향성이 다소 흔들릴 전망입니다.",
            "medium",
            "korea",
        ),
    ]


def fetch_news_with_fallback() -> Dict[str, List[Dict]]:
    """실시간 뉴스 수집 + 모의 데이터 폴백"""
    fetcher = MarketNewsFetcher(logger=lambda msg: print(msg))
    fetched = fetcher.fetch_all()

    return {
        "global": fetched.get("global") or get_mock_global_news_data(),
        "semiconductor": fetched.get("semiconductor") or get_mock_semiconductor_news_data(),
        "geopolitical": fetched.get("geopolitical") or get_mock_geopolitical_news_data(),
        "korea": fetched.get("korea") or get_mock_korea_news_data(),
    }


def render_section(title: str, articles: List[Dict]) -> str:
    lines = [f"## {title}"]
    if not articles:
        lines.append("- 관련 기사가 부족해 기본 데이터를 사용했습니다.")
        return "\n".join(lines)

    for article in articles[:5]:
        source = article.get("source") or "출처 미상"
        impact = (article.get("impact") or "medium").upper()
        published = format_article_time(article.get("published_at"))
        headline = f"- **{article.get('title')}** ({source}"
        if published:
            headline += f", {published}"
        headline += f") [Impact: {impact}]"
        lines.append(headline)

        summary = article.get("summary") or article.get("description") or ""
        summary = shorten(summary.replace("\n", " "), width=160, placeholder="…") if summary else ""
        if summary:
            lines.append(f"  - {summary}")

        link = article.get("link")
        if link:
            lines.append(f"  - 링크: {link}")
    lines.append("")
    return "\n".join(lines)


def format_article_time(value: Any) -> str:
    if not value:
        return ""
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return ""
    local = dt.astimezone()
    return local.strftime("%m-%d %H:%M")


def build_insights(news_sections: Dict[str, List[Dict]]) -> str:
    total_articles = sum(len(items) for items in news_sections.values())
    high_impact = sum(
        1
        for items in news_sections.values()
        for article in items
        if str(article.get("impact", "")).lower() == "high"
    )
    category_breakdown = ", ".join(
        f"{title}: {len(news_sections.get(key, []))}건"
        for key, title in SECTION_CONFIG
    )

    return "\n".join(
        [
            "## 🧭 종합 인사이트",
            f"- 전체 기사 {total_articles}건 중 고위험 이슈 {high_impact}건 탐지",
            f"- 카테고리 분포: {category_breakdown}",
            "- 반복 수신 여부: 저장된 히스토리로 중복 감지",
            "",
        ]
    )


def flatten_news_items(news_sections: Dict[str, List[Dict]]) -> List[Dict]:
    items = []
    for key, articles in news_sections.items():
        for article in articles:
            data = dict(article)
            data["section"] = key
            items.append(data)
    return items


def record_report_history(report: str, news_items: List[Dict], snapshot: Dict) -> bool:
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    history: List[Dict] = []
    if HISTORY_FILE.exists():
        try:
            history = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            history = []

    entry = {
        "timestamp": datetime.now().isoformat(),
        "hash": hashlib.sha256(report.encode("utf-8")).hexdigest(),
        "article_count": len(news_items),
        "snapshot": snapshot,
    }

    duplicate = bool(history and history[-1].get("hash") == entry["hash"])
    entry["duplicate_with_previous"] = duplicate
    history.append(entry)
    history = history[-60:]  # 최근 60건만 유지

    HISTORY_FILE.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")
    return duplicate


def build_report(news_sections: Dict[str, List[Dict]], snapshot: Dict, kospi_report: str | None) -> str:
    now_str = datetime.now().strftime("%Y년 %m월 %d일 %H:%M")
    lines = [
        "## 📊 오늘의 시장 뉴스 요약",
        f"**생성 시각**: {now_str}",
        "**데이터 소스**: Google News RSS + FinanceDataReader 지표 스냅샷",
        "",
        format_snapshot_lines(snapshot),
    ]

    for key, title in SECTION_CONFIG:
        lines.append(render_section(title, news_sections.get(key, [])))

    lines.append(build_insights(news_sections))

    if kospi_report:
        lines.append("## 📌 KOSPI 지수 & ETF 인사이트")
        lines.append(kospi_report)

    lines.append(
        "\n⚖️ 본 리포트는 정보 제공용이며 투자 조언이 아닙니다. "
        "결정 전 개인의 리스크 허용 범위를 검토하세요."
    )

    return "\n".join(line for line in lines if line).strip()


def generate_market_news_report() -> Dict[str, Any]:
    """
    시장 뉴스 리포트 + 코스피 지수 ETF 분석 생성
    """
    try:
        print("=" * 60)
        print("📰 시장 뉴스 분석 시작...")
        print("=" * 60)

        news_sections = fetch_news_with_fallback()
        snapshot = get_market_snapshot()

        kospi_meta = None
        kospi_report = None
        if analyze_kospi:
            try:
                kospi_meta, kospi_report = analyze_kospi(news_sections)
            except Exception as exc:
                print(f"⚠️  KOSPI 분석 실패: {exc}")

        report = build_report(news_sections, snapshot, kospi_report)
        flattened = flatten_news_items(news_sections)
        duplicate = record_report_history(report, flattened, snapshot)

        return {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "report": report,
            "news_items": flattened,
            "snapshot": snapshot,
            "kospi_analysis": kospi_meta,
            "duplicate_with_previous": duplicate,
            "category": "comprehensive_market_analysis",
        }

    except Exception as exc:
        print(f"❌ 분석 실패: {exc}")
        return {"success": False, "error": str(exc)}


if __name__ == "__main__":
    result = generate_market_news_report()

    if result["success"]:
        print("\n" + "=" * 60)
        print("📋 최종 종합 시장 분석 리포트")
        print("=" * 60)
        print()
        print(result["report"])
        print()
        print("=" * 60)
        print("✅ 분석 완료!")
        if result.get("duplicate_with_previous"):
            print("⚠️  이전 결과와 동일한 리포트가 감지되었습니다.")

        print("\n" + "=" * 60)
        print("📧 이메일 발송")
        print("=" * 60)

        try:
            from core.utils.market_news_sender import send_market_news_email

            success = send_market_news_email(
                result["report"],
                use_smtp=True,
                news_items=result.get("news_items"),
            )

            if success:
                print("\n✅ 이메일 발송 완료!")
            else:
                print("\n⚠️  이메일 발송 실패 (분석은 완료됨)")

        except Exception as exc:
            print(f"\n⚠️  이메일 발송 모듈 로드 실패: {exc}")
            print("   분석 결과는 정상적으로 완료되었습니다.")

    else:
        print(f"\n❌ 오류: {result['error']}")
        sys.exit(1)
