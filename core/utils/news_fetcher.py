"""
실시간 뉴스 수집 유틸리티

Google News RSS 및 NewsAPI(옵션)를 활용해
시장 뉴스 카테고리별 기사 목록을 반환한다.
"""

from __future__ import annotations

import html
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Dict, List, Optional
from urllib.parse import quote_plus

import requests
import xml.etree.ElementTree as ET


GOOGLE_NEWS_BASE = "https://news.google.com/rss/search"


@dataclass
class NewsArticle:
    title: str
    link: str
    source: str
    published_at: Optional[datetime]
    summary: str
    category: str
    impact: str = "medium"

    def to_dict(self) -> Dict:
        return {
            "title": self.title,
            "link": self.link,
            "source": self.source,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "summary": self.summary,
            "description": self.summary,
            "category": self.category,
            "impact": self.impact,
        }


class MarketNewsFetcher:
    """RSS/NewsAPI 기반 시장 뉴스 수집기"""

    DEFAULT_CONFIG = {
        "global": {
            "queries": [
                "KOSPI 금리 when:24h",
                "Fed 금리 논의 when:24h",
                "S&P 500 증시 when:24h",
            ],
            "impact": "high",
            "newsapi_query": "global markets OR fed rate decision",
        },
        "semiconductor": {
            "queries": [
                "반도체 소식 when:24h",
                "삼성전자 생산 when:24h",
                "SK Hynix 메모리 when:24h",
            ],
            "impact": "high",
            "newsapi_query": "semiconductor OR chip market korea",
        },
        "geopolitical": {
            "queries": [
                "지정학 리스크 when:24h",
                "미중 갈등 when:24h",
                "러시아 우크라이나 전쟁 when:24h",
            ],
            "impact": "medium",
            "newsapi_query": "geopolitics korea market",
        },
        "korea": {
            "queries": [
                "코스피 증시 when:24h",
                "한국은행 금리 when:24h",
                "원달러 환율 when:24h",
            ],
            "impact": "medium",
            "newsapi_query": "Korean stock market OR Bank of Korea",
        },
    }

    def __init__(self, session: Optional[requests.Session] = None, logger=None):
        self.session = session or requests.Session()
        self.session.headers.update(
            {
                "User-Agent": os.getenv(
                    "MARKET_NEWS_USER_AGENT",
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/118.0 Safari/537.36",
                )
            }
        )
        self.logger = logger or (lambda *args, **kwargs: None)
        self.per_query_limit = int(os.getenv("MARKET_NEWS_ITEMS_PER_QUERY", "5"))
        self.per_category_limit = int(os.getenv("MARKET_NEWS_ITEMS_PER_CATEGORY", "6"))
        self.newsapi_key = os.getenv("NEWSAPI_KEY")
        self.newsapi_endpoint = os.getenv(
            "NEWSAPI_ENDPOINT", "https://newsapi.org/v2/everything"
        )

    def fetch_all(self) -> Dict[str, List[Dict]]:
        """카테고리별 뉴스 기사 목록 반환"""
        results: Dict[str, List[Dict]] = {}
        for category, config in self.DEFAULT_CONFIG.items():
            articles: List[NewsArticle] = []

            if self.newsapi_key and config.get("newsapi_query"):
                api_articles = self._fetch_newsapi(
                    config["newsapi_query"], category, config["impact"]
                )
                articles.extend(api_articles)

            for query in config["queries"]:
                rss_articles = self._fetch_rss(query, category, config["impact"])
                articles.extend(rss_articles)

            deduped = self._deduplicate(articles)
            results[category] = [article.to_dict() for article in deduped]

        return results

    def _fetch_rss(
        self, query: str, category: str, impact: str
    ) -> List[NewsArticle]:
        """Google News RSS 검색"""
        url = (
            f"{GOOGLE_NEWS_BASE}?q={quote_plus(query)}&hl=ko&gl=KR&ceid=KR:ko"
        )
        try:
            resp = self.session.get(url, timeout=10)
            resp.raise_for_status()
        except Exception as exc:
            self.logger(f"[MarketNewsFetcher] RSS fetch failed for {query}: {exc}")
            return []

        try:
            root = ET.fromstring(resp.content)
        except ET.ParseError as exc:
            self.logger(f"[MarketNewsFetcher] RSS parse error for {query}: {exc}")
            return []

        items = []
        for item in root.findall(".//item"):
            title = (item.findtext("title") or "").strip()
            link = (item.findtext("link") or "").strip()
            description = html.unescape((item.findtext("description") or "").strip())
            source = (item.findtext("source") or "Google News").strip()
            pub_date = self._parse_pub_date(item.findtext("pubDate"))

            if not title:
                continue

            items.append(
                NewsArticle(
                    title=title,
                    link=link,
                    source=source or "Google News",
                    published_at=pub_date,
                    summary=description,
                    category=category,
                    impact=impact,
                )
            )
            if len(items) >= self.per_query_limit:
                break

        return items

    def _fetch_newsapi(
        self, query: str, category: str, impact: str
    ) -> List[NewsArticle]:
        """NewsAPI 연동 (API 키 설정 시)"""
        params = {
            "q": query,
            "language": "ko",
            "pageSize": self.per_category_limit,
            "sortBy": "publishedAt",
            "apiKey": self.newsapi_key,
        }
        try:
            resp = self.session.get(self.newsapi_endpoint, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            self.logger(f"[MarketNewsFetcher] NewsAPI request failed: {exc}")
            return []

        articles = []
        for article in data.get("articles", []):
            title = (article.get("title") or "").strip()
            if not title:
                continue
            url = article.get("url") or ""
            summary = (article.get("description") or "").strip()
            published_at = self._parse_pub_date(article.get("publishedAt"))
            source = ""
            if isinstance(article.get("source"), dict):
                source = article["source"].get("name") or ""
            source = source or "NewsAPI"

            articles.append(
                NewsArticle(
                    title=title,
                    link=url,
                    source=source,
                    published_at=published_at,
                    summary=summary,
                    category=category,
                    impact=impact,
                )
            )

        return articles

    def _deduplicate(self, articles: List[NewsArticle]) -> List[NewsArticle]:
        """제목 기준 중복 제거 및 최신순 정렬"""
        seen = set()
        cleaned: List[NewsArticle] = []
        for article in sorted(
            articles, key=lambda a: a.published_at or datetime.now(timezone.utc), reverse=True
        ):
            title_key = article.title.strip()
            if title_key in seen:
                continue
            seen.add(title_key)
            cleaned.append(article)
            if len(cleaned) >= self.per_category_limit:
                break
        return cleaned

    @staticmethod
    def _parse_pub_date(value: Optional[str]) -> Optional[datetime]:
        if not value:
            return None
        try:
            dt = parsedate_to_datetime(value)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except Exception:
            return None


__all__ = ["MarketNewsFetcher", "NewsArticle"]
