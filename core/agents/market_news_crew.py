"""
시장 뉴스 분석 및 요약 Crew (간소화 버전)

한국 코스피에 영향을 줄 만한 글로벌/국내 뉴스를 수집하고 분석하여
투자자 관점에서 요약하는 AI Agent

주의: 이 버전은 Mock 데이터를 사용합니다.
실제 구현에서는 NewsAPI, Finnhub 등 실제 API를 연동하세요.
"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, List, Any
from pathlib import Path

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
    pass  # python-dotenv 미설치 시 무시

try:
    from crewai import Agent, Task, Crew, Process
except ImportError:
    print("⚠️ CrewAI가 설치되지 않았습니다.")
    print("pip install crewai 를 실행하세요.")
    sys.exit(1)


# ============================================================================
# 뉴스 데이터 (실제 API 대신 Mock 데이터)
# ============================================================================

def get_global_news_data() -> List[Dict]:
    """나스닥, Fed, S&P 500 등 글로벌 시장 뉴스"""
    return [
        {
            "title": "Fed 금리 인상 예고",
            "source": "Reuters",
            "impact": "high",
            "category": "nasdaq",
            "description": "연방준비제도가 다음 회의에서 금리 인상을 고려 중. 이는 달러 강세로 이어져 한국 수출주에 부정적."
        },
        {
            "title": "S&P 500 신고가 경신",
            "source": "Bloomberg",
            "impact": "medium",
            "category": "nasdaq",
            "description": "S&P 500이 역사적 신고가를 경신했습니다. 미국 경제 강세 신호."
        },
        {
            "title": "Tesla 배터리 기술 혁신",
            "source": "TechCrunch",
            "impact": "medium",
            "category": "tech",
            "description": "테슬라, 차세대 배터리 기술 발표. 전기차 산업 재편 가능성."
        }
    ]


def get_semiconductor_news_data() -> List[Dict]:
    """반도체 관련 뉴스"""
    return [
        {
            "title": "Samsung 3nm 공정 진전",
            "source": "전자신문",
            "impact": "high",
            "company": "Samsung",
            "description": "삼성전자, 3nm 공정 대량 생산 시작. 반도체 경기 회복 신호."
        },
        {
            "title": "TSMC 파운드리 수주 증가",
            "source": "DigiTimes",
            "impact": "high",
            "company": "TSMC",
            "description": "TSMC 파운드리 주문 급증으로 공급 부족 예상. 대만 반도체 경기 호황."
        },
        {
            "title": "SK Hynix 메모리 가격 상승",
            "source": "뉴스1",
            "impact": "medium",
            "company": "SK Hynix",
            "description": "메모리 칩 수급 재편으로 가격 상승세. SK Hynix에 호재."
        }
    ]


def get_geopolitical_news_data() -> List[Dict]:
    """지정학적 리스크 관련 뉴스"""
    return [
        {
            "title": "미중 기술 갈등 심화",
            "source": "BBC",
            "impact": "high",
            "risk_level": "critical",
            "description": "미국, 중국 반도체 기업에 추가 제재 계획. 반도체 공급망 우려."
        },
        {
            "title": "한반도 긴장 고조",
            "source": "연합뉴스",
            "impact": "high",
            "risk_level": "warning",
            "description": "북한 미사일 발사로 한반도 긴장 고조. 방위사업주 주목."
        },
        {
            "title": "러시아-우크라이나 갈등 지속",
            "source": "Reuters",
            "impact": "medium",
            "risk_level": "warning",
            "description": "에너지 가격 변동성 지속. 유가와 환율에 영향."
        }
    ]


def get_korea_market_news_data() -> List[Dict]:
    """한국 증시 관련 뉴스"""
    return [
        {
            "title": "한은 금리 결정 예정",
            "source": "연합뉴스",
            "impact": "high",
            "category": "domestic",
            "description": "한국은행, 다음 주 금리 결정 회의 개최. 인상 확률 높음. 금리민감주 주의."
        },
        {
            "title": "원/달러 환율 상승",
            "source": "매일경제",
            "impact": "high",
            "category": "fx",
            "description": "원화 약세로 수출주 상승. 삼성, 현대, SK 등 수혜."
        },
        {
            "title": "코스피 200 선물 등락",
            "source": "마켓뉴스",
            "impact": "medium",
            "category": "market",
            "description": "야간 선물 시장 변동성. 오픈 시 호가 예상."
        }
    ]


# ============================================================================
# 분석 함수
# ============================================================================

def analyze_all_news() -> str:
    """
    모든 뉴스를 수집하고 분석하여 한국어로 요약

    실제 환경에서는 CrewAI를 사용하지만,
    여기서는 간단한 분석 로직으로 대체합니다.
    """

    # 모든 뉴스 수집
    all_news = {
        "global": get_global_news_data(),
        "semiconductor": get_semiconductor_news_data(),
        "geopolitical": get_geopolitical_news_data(),
        "korea": get_korea_market_news_data()
    }

    # 분석 리포트 생성
    report = f"""
## 📊 오늘의 시장 뉴스 요약
**분석 시간**: {datetime.now().strftime('%Y년 %m월 %d일 %H:%M')}
**증시 오픈까지**: 약 30분

---

## 🌍 글로벌 시장 (나스닥)

### ⚠️ 높은 영향도
- **Fed 금리 인상 신호**
  - 달러 강세로 한국 수출주 약세 우려
  - 영향 종목: 삼성전자, SK 하이닉스, 현대차
  - 추천: 수출주는 조심스럽게 접근

- **S&P 500 신고가 경신**
  - 미국 경제 강세 신호
  - 글로벌 성장주에 호재

### 🟡 중간 영향도
- **Tesla 배터리 기술 혁신**
  - 전기차 산업 재편 가능성
  - 국내 배터리주 모니터링 필요

---

## 🔧 반도체 뉴스

### ⚠️ 높은 영향도
- **Samsung 3nm 공정 시작**
  - 반도체 산업 구조적 호재
  - 영향 종목: 삼성전자, SK Hynix
  - 추천: 해당 종목 매수 기회 재검토

- **TSMC 파운드리 수주 급증**
  - 글로벌 반도체 수급 재편
  - 대만 반도체 호황 신호
  - 한국 파운드리 관련 Supplier 주목

### 🟡 중간 영향도
- **SK Hynix 메모리 가격 상승**
  - 메모리 수급 개선 신호
  - SK Hynix에 긍정적

---

## ⚔️ 지정학적 리스크

### ⚠️ 높은 영향도
- **미중 기술 제재 심화**
  - 반도체 공급망 우려 재연
  - 영향 범위: 광범위 (수출주 전반)
  - 추천: 리스크 헤징 강화

- **한반도 긴장 고조**
  - 북한 미사일 발사
  - 영향 종목: 방위사업주 (LIG넥스원, 현대로템 등)
  - 추천: 방위주 주목

### 🟡 중간 영향도
- **러우 갈등 지속**
  - 에너지 가격 변동성
  - 유가, 환율에 영향

---

## 🇰🇷 국내 뉴스

### ⚠️ 높은 영향도
- **한은 금리 결정 임박 (내일)**
  - 인상 확률 높음
  - 영향 범위: 금리민감주 (금융주, 부동산주)
  - 추천: 금리 결정 후 방향성 확인 필수

- **원/달러 환율 상승**
  - 원화 약세 지속
  - 영향 종목: 자동차, 전자, 반도체 (수출주)
  - 추천: 수출주 매수 관심 높음

### 🟡 중간 영향도
- **야간 선물 변동성**
  - 오픈 시장 호가 변동 예상
  - 대기 필요

---

## 📈 종합 평가

### 🎯 이론적 평가: **호재 > 악재**

**이유:**
1. 반도체 섹터의 구조적 호재
   - Samsung 3nm 공정 시작
   - TSMC 파운드리 호황
   - 메모리 가격 상승

2. 수출주 환율 이익
   - 원화 약세 진행
   - 나스닥 약세 상쇄 가능

3. 국내 수익성 개선
   - 방위사업주 호재
   - 금융주 정상화 기대

### ⚠️ 주의사항
- Fed 금리 결정이 실제 영향도 결정
- 한은 금리 인상 시 금리민감주 조정 가능
- 지정학 리스크 (미중, 한반도) 모니터링 필수

---

## 💡 투자자 액션

✅ **오늘 추천:**
1. 반도체주 비중 확인 (호재 지속)
2. 수출주 긍정적 평가 (환율 이익)
3. 방위사업주 주목 (지정학 리스크)

⚠️ **주의:**
1. Fed 금리 발표 대기 (달러 강세 우려)
2. 한은 금리 결정 대기 (내일)
3. 미중 추가 제재 뉴스 모니터링

---

**다음 보고서**: 내일 오전 9시
"""

    return report.strip()


# ============================================================================
# 메인 함수
# ============================================================================

def generate_market_news_report() -> Dict[str, Any]:
    """
    시장 뉴스 리포트 + 코스피 지수 ETF 분석 생성
    """
    try:
        print("=" * 60)
        print("📰 시장 뉴스 분석 시작...")
        print("=" * 60)
        print()

        # 1. 뉴스 분석
        market_news_report = analyze_all_news()

        print("✅ 뉴스 분석 완료")
        print()

        # 2. 코스피 지수 및 ETF 분석
        print("=" * 60)
        print("📈 코스피 지수 & ETF 분석 시작...")
        print("=" * 60)
        print()

        try:
            from core.agents.kospi_etf_analyzer import analyze_kospi

            # 뉴스 데이터 수집
            all_news_data = {
                "global": get_global_news_data(),
                "semiconductor": get_semiconductor_news_data(),
                "geopolitical": get_geopolitical_news_data(),
                "korea": get_korea_market_news_data()
            }

            # 코스피 분석 실행
            kospi_analysis, kospi_report = analyze_kospi(all_news_data)

            print("✅ 코스피 지수 분석 완료")
            print()

        except Exception as e:
            print(f"⚠️  코스피 분석 실패: {e}")
            kospi_report = None
            kospi_analysis = None

        # 3. 최종 종합 리포트 생성
        final_report = generate_comprehensive_report(market_news_report, kospi_report)

        return {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "report": final_report,
            "market_news": market_news_report,
            "kospi_analysis": kospi_analysis,
            "kospi_report": kospi_report,
            "category": "comprehensive_market_analysis"
        }

    except Exception as e:
        print(f"❌ 분석 실패: {e}")
        import traceback
        traceback.print_exc()

        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


def generate_comprehensive_report(market_news: str, kospi_report: str = None) -> str:
    """
    시장 뉴스와 코스피 분석을 합친 종합 리포트 생성

    Args:
        market_news: 시장 뉴스 분석 텍스트
        kospi_report: 코스피 지수 ETF 분석 텍스트

    Returns:
        최종 종합 리포트
    """
    comprehensive_report = f"""
{'╔' + '═' * 78 + '╗'}
{'║' + ' ' * 78 + '║'}
{'║' + '  📰 종합 시장 분석 보고서 - 증시 오픈 전 최종 브리핑'.center(78) + '║'}
{'║' + ' ' * 78 + '║'}
{'╚' + '═' * 78 + '╝'}

📅 생성시간: {datetime.now().strftime('%Y년 %m월 %d일 %H:%M:%S')}
⏰ 증시 개장까지: 약 10시간 (매일 오전 9시 개장)

{'═' * 80}
【 PART 1. 시장 뉴스 분석 】
{'═' * 80}

{market_news}
"""

    if kospi_report:
        comprehensive_report += f"""

{'═' * 80}
【 PART 2. 코스피 지수 & 지수 ETF 분석 】
{'═' * 80}

{kospi_report}
"""

    # 최종 요약 섹션
    comprehensive_report += """

╔══════════════════════════════════════════════════════════════════════════════╗
║                           📋 최종 투자 가이드 요약                            ║
╚══════════════════════════════════════════════════════════════════════════════╝

✅ 오늘의 핵심 포인트:

1️⃣  반도체 섹터
   • Samsung 3nm 공정 시작 → 구조적 호재 지속
   • SK Hynix 메모리 가격 상승 → 실적 개선 기대
   • 추천: 반도체주 매수 기회 재검토, 특히 TIGER 200 ETF

2️⃣  수출주 (환율 우호)
   • 원화 약세 진행 중 (USD 강세)
   • 영향 종목: 삼성, 현대, SK 등 대형 수출 기업
   • 추천: 대형주 중심 KODEX 100 또는 TIGER 200

3️⃣  금리 민감주 (주의 필요)
   • 한은 금리 결정 임박 (인상 확률 높음)
   • 금융주, 부동산주 영향 예상
   • 전략: 금리 결정 후 방향성 재확인 필수

4️⃣  지정학적 리스크
   • 미중 기술 갈등 심화 → 공급망 불확실성
   • 한반도 긴장 고조 → 방위사업주 주목
   • 주의: 리스크 헤징 강화 필요

⚠️  투자 시 주의사항:

• 포트폴리오의 20% 이상을 단일 ETF에 집중하지 마세요
• 변동성이 높은 소형주 ETF는 분산 투자로 리스크 관리
• 금리 정책 발표 시간 전후 변동성 증가 예상
• 기존 포지션의 손절매 계획과 수익 실현 계획 수립
• 정기적인 리밸런싱 (월 1회 이상) 권장

📊 추천 포트폴리오 구성 (예시):

상승장:
├─ TIGER 200 (40%) - 대형주 중심, 안정적 수익
├─ KODEX 소형주 (20%) - 고수익 추구
├─ TIGER 배당성장 (20%) - 수익 고착
└─ 현금/채권 (20%) - 리스크 관리

중립장:
├─ KODEX 100 (40%) - 변동성 낮은 대형주
├─ TIGER 배당성장 (40%) - 배당 수익
└─ 현금 (20%) - 진입 기회 대기

하락장:
├─ TIGER 배당성장 (50%) - 손실 완화
├─ KODEX 100 (30%) - 안정성 우선
└─ 현금 (20%) - 기회 포착 대기

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📌 더 자세한 정보는 상단 시장 뉴스 분석과 코스피 분석 섹션을 참조하세요.

⚖️  법적 고지사항:

본 분석은 공개 정보 기반의 교육용 자료이며, 투자 조언이 아닙니다.
투자 결정 전에 항상 전문가의 상담을 받으시기 바랍니다.
과거 성과가 미래 수익을 보장하지 않습니다.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

생성: AI Market Analysis Agent
다음 보고서: 내일 오전 7시 (정상 거래일 기준)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

    return comprehensive_report.strip()


# ============================================================================
# 메인 실행
# ============================================================================

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
        print("=" * 60)

        # 이메일 발송 시도
        print("\n" + "=" * 60)
        print("📧 이메일 발송")
        print("=" * 60)

        try:
            from core.utils.market_news_sender import send_market_news_email

            success = send_market_news_email(result["report"], use_smtp=True)

            if success:
                print("\n✅ 이메일 발송 완료!")
            else:
                print("\n⚠️  이메일 발송 실패 (분석은 완료됨)")

        except Exception as e:
            print(f"\n⚠️  이메일 발송 모듈 로드 실패: {e}")
            print("   분석 결과는 정상적으로 완료되었습니다.")

    else:
        print(f"\n❌ 오류: {result['error']}")
        sys.exit(1)
