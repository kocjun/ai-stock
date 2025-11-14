"""
업종별 대장주 투자 전략

한국 주식시장 주요 5개 업종의 대장주에 집중 투자하는 전략
"""

from typing import Dict, List, Tuple
from datetime import datetime
import sys
from pathlib import Path

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from core.utils.db_utils import get_db_connection


# 한국 주식시장 주요 5개 업종 및 대장주 정의
SECTOR_LEADERS = {
    "반도체/전기전자": {
        "leaders": [
            {"code": "005930", "name": "삼성전자", "priority": 1},
            {"code": "000660", "name": "SK하이닉스", "priority": 2}
        ],
        "description": "국내 최대 수출 산업, 글로벌 경쟁력 보유"
    },
    "자동차/운수장비": {
        "leaders": [
            {"code": "005380", "name": "현대차", "priority": 1},
            {"code": "000270", "name": "기아", "priority": 2}
        ],
        "description": "전기차 전환 수혜, 글로벌 판매 확대"
    },
    "화학": {
        "leaders": [
            {"code": "051910", "name": "LG화학", "priority": 1},
            {"code": "011170", "name": "롯데케미칼", "priority": 2}
        ],
        "description": "배터리 소재, 석유화학 중심"
    },
    "금융": {
        "leaders": [
            {"code": "105560", "name": "KB금융", "priority": 1},
            {"code": "055550", "name": "신한지주", "priority": 2}
        ],
        "description": "금리 상승 수혜, 안정적 배당"
    },
    "IT/인터넷": {
        "leaders": [
            {"code": "035420", "name": "네이버", "priority": 1},
            {"code": "035720", "name": "카카오", "priority": 2}
        ],
        "description": "플랫폼 경제, 디지털 전환 수혜"
    }
}


def get_sector_leader_recommendations(
    num_sectors: int = 5,
    leaders_per_sector: int = 1
) -> List[Dict]:
    """
    업종별 대장주 추천 생성

    Args:
        num_sectors: 선택할 업종 수 (기본: 5개 전체)
        leaders_per_sector: 업종당 대장주 수 (1=1등만, 2=1,2등)

    Returns:
        추천 종목 리스트 (trading_crew.py 포맷과 동일)
    """
    recommendations = []

    # 선택된 업종들
    selected_sectors = list(SECTOR_LEADERS.keys())[:num_sectors]

    # 총 종목 수 계산 (동일 가중치용)
    total_stocks = num_sectors * leaders_per_sector
    equal_weight = 1.0 / total_stocks

    print(f"\n{'='*80}")
    print(f"업종별 대장주 투자 전략")
    print(f"{'='*80}\n")
    print(f"선택 업종: {num_sectors}개")
    print(f"업종당 종목: {leaders_per_sector}개")
    print(f"총 종목 수: {total_stocks}개")
    print(f"종목당 비중: {equal_weight*100:.1f}%\n")

    for sector_name in selected_sectors:
        sector_info = SECTOR_LEADERS[sector_name]
        leaders = sector_info["leaders"][:leaders_per_sector]

        print(f"[{sector_name}] {sector_info['description']}")

        for leader in leaders:
            recommendations.append({
                'code': leader['code'],
                'name': leader['name'],
                'weight': equal_weight,
                'sector': sector_name,
                'reason': f"{sector_name} 대장주 ({leader['priority']}순위)"
            })
            print(f"  • {leader['name']} ({leader['code']}) - {equal_weight*100:.1f}%")

        print()

    return recommendations


def analyze_sector_leader_strategy_risks() -> Dict:
    """
    업종별 대장주 전략의 위험 요소 분석

    Returns:
        위험 분석 결과
    """
    risks = {
        "전략_개요": {
            "유형": "업종별 대장주 집중 투자",
            "목표": "주요 업종의 시장 지배적 기업에 투자",
            "방식": "5개 업종 × 1-2개 대장주 = 5-10개 종목"
        },

        "주요_장점": {
            "높은_유동성": {
                "설명": "대장주는 거래량이 많아 원하는 시점에 매매 가능",
                "중요도": "상"
            },
            "정보_투명성": {
                "설명": "대형주는 애널리스트 리포트와 뉴스가 풍부",
                "중요도": "상"
            },
            "기업_안정성": {
                "설명": "각 업종의 선두기업으로 재무구조 견고",
                "중요도": "상"
            },
            "업종_대표성": {
                "설명": "업종 전체의 방향성을 대표하는 종목들",
                "중요도": "중"
            }
        },

        "주요_위험": {
            "1_집중_리스크": {
                "위험도": "상",
                "설명": "5-10개 종목만으로 구성되어 분산 효과 제한적",
                "영향": "개별 종목의 급락이 포트폴리오에 큰 타격",
                "완화_방안": [
                    "업종당 2개씩 선정하여 10개 종목으로 확대",
                    "각 종목 비중을 10% 이하로 제한",
                    "손절 기준을 엄격히 설정 (예: -7%)"
                ]
            },

            "2_업종_상관성": {
                "위험도": "중상",
                "설명": "선택한 5개 업종이 동시에 하락할 가능성",
                "세부_리스크": {
                    "경기_민감도": "반도체, 자동차, 화학은 경기 순환에 민감",
                    "수출_의존도": "한국 대장주 대부분이 수출 중심",
                    "달러_영향": "환율 변동에 따른 동반 움직임"
                },
                "완화_방안": [
                    "방어적 업종(금융) 비중 조정",
                    "경기 선행 지표 모니터링",
                    "글로벌 경제 상황 주시"
                ]
            },

            "3_대장주_프리미엄": {
                "위험도": "중",
                "설명": "대장주는 이미 높은 밸류에이션으로 거래",
                "영향": "추가 상승 여력 제한, 조정 시 낙폭 확대",
                "완화_방안": [
                    "밸류에이션 지표(PER, PBR) 모니터링",
                    "과열 구간에서는 비중 축소",
                    "실적 발표 전후 변동성 대비"
                ]
            },

            "4_중소형주_대비_성과": {
                "위험도": "중",
                "설명": "시장 상승기에 중소형주 대비 수익률 저조 가능",
                "영향": "상대적 기회비용 발생",
                "판단_기준": "안정성 vs 수익성 trade-off 수용 여부"
            },

            "5_섹터_로테이션": {
                "위험도": "중",
                "설명": "시장 국면에 따라 특정 업종이 소외될 수 있음",
                "예시": {
                    "금리_상승기": "IT/인터넷 업종 부진",
                    "경기_침체기": "자동차, 화학 업종 부진",
                    "수출_부진기": "반도체 업종 부진"
                },
                "완화_방안": [
                    "분기별 업종 로테이션 점검",
                    "부진 업종 비중 축소 고려",
                    "거시경제 지표 기반 업종 교체"
                ]
            },

            "6_단일_이슈_리스크": {
                "위험도": "중상",
                "설명": "대장주 하나의 악재가 전체 포트폴리오에 큰 영향",
                "실제_사례": "카카오 김범수 구속(2024), 삼성전자 실적 쇼크",
                "완화_방안": [
                    "일일 모니터링 강화",
                    "뉴스/공시 즉각 대응",
                    "자동 손절 시스템 가동"
                ]
            },

            "7_AI_추천_무시": {
                "위험도": "중",
                "설명": "AI가 발굴한 가치주/성장주를 놓칠 수 있음",
                "영향": "데이터 기반 최적화 포기",
                "trade_off": "단순성/안정성 vs AI 인사이트"
            }
        },

        "정량적_위험_지표": {
            "추정_변동성": {
                "값": "연 20-25%",
                "근거": "대형주 평균 변동성",
                "비교": "KOSPI 지수 대비 유사"
            },
            "최대_낙폭_MDD": {
                "정상_시": "15-20%",
                "위기_시": "30-40%",
                "근거": "2020 코로나, 2022 금리 인상기 경험"
            },
            "업종_상관계수": {
                "평균": "0.6-0.7",
                "의미": "업종 간 분산 효과 제한적",
                "비교": "30개 분산 시 0.4-0.5"
            },
            "샤프_비율": {
                "추정": "0.4-0.6",
                "의미": "중간 수준의 위험대비 수익",
                "개선_방안": "손절/익절 규칙 엄격화"
            }
        },

        "권장_리스크_관리": {
            "포지션_관리": [
                "업종당 20% 상한 (5개 업종 → 자동 충족)",
                "종목당 15% 상한 (업종당 2개 → 자동 충족)",
                "현금 비중 10-20% 유지"
            ],
            "손익_관리": [
                "개별 종목 손절: -7% (대장주는 -10%까지 완화 가능)",
                "개별 종목 익절: +20%",
                "포트폴리오 손절: 총 자산 -15%"
            ],
            "리밸런싱": [
                "분기별 정기 리밸런싱",
                "비중 5%p 이탈 시 조정",
                "업종 교체는 반기 1회 검토"
            ],
            "모니터링": [
                "일일: 개별 종목 뉴스/공시",
                "주간: 업종별 성과 점검",
                "월간: 거시경제 지표 분석",
                "분기: 실적 발표 점검"
            ]
        },

        "AI_전략_대비_평가": {
            "AI_전략_장점": [
                "데이터 기반 종목 발굴",
                "밸류에이션 고려",
                "모멘텀 팩터 활용",
                "편향 없는 선택"
            ],
            "대장주_전략_장점": [
                "단순하고 이해하기 쉬움",
                "유동성 높아 실행 용이",
                "안정적 기업 위주",
                "감정적 신뢰도 높음"
            ],
            "권장_사항": "두 전략을 혼합하는 하이브리드 접근",
            "혼합_방안": {
                "옵션1": "70% 대장주 + 30% AI 추천",
                "옵션2": "5개 대장주 + AI 추천 5개 = 10개",
                "옵션3": "분기별 전략 교체 (A/B 테스트)"
            }
        },

        "결론_및_권고": {
            "적합한_투자자": [
                "주식 투자 초보자",
                "안정성 우선 투자자",
                "장기 투자 지향",
                "대형주 선호"
            ],
            "부적합한_투자자": [
                "고수익 추구 투자자",
                "단기 트레이딩 선호",
                "중소형주 선호",
                "적극적 매매 원하는 투자자"
            ],
            "종합_평가": {
                "안정성": "★★★★☆ (4/5)",
                "수익성": "★★★☆☆ (3/5)",
                "분산성": "★★☆☆☆ (2/5)",
                "유동성": "★★★★★ (5/5)",
                "단순성": "★★★★★ (5/5)"
            },
            "최종_권고": """
            업종별 대장주 전략은 안정성과 단순성이 장점이지만,
            5-10개 종목으로는 분산 효과가 제한적입니다.

            권장 사항:
            1. 업종당 2개씩 → 총 10개 종목으로 확대
            2. 손절 규칙 엄격 준수 (-7% 또는 -10%)
            3. 분기별 업종 로테이션 점검
            4. AI 추천과 50:50 혼합 고려 (총 15-20개 종목)
            5. 최소 6개월 이상 장기 투자 관점 유지

            이 전략은 '안전한 성장'을 추구하는 투자자에게 적합하며,
            '공격적 수익'을 원한다면 AI 전략을 우선 고려하세요.
            """
        }
    }

    return risks


def print_risk_analysis():
    """위험 분석 결과를 보기 좋게 출력"""
    risks = analyze_sector_leader_strategy_risks()

    print(f"\n{'='*80}")
    print(f"업종별 대장주 투자 전략 - 위험성 분석 보고서")
    print(f"{'='*80}\n")
    print(f"생성 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # 1. 전략 개요
    print(f"{'─'*80}")
    print(f"1. 전략 개요")
    print(f"{'─'*80}")
    overview = risks['전략_개요']
    for key, value in overview.items():
        print(f"  • {key}: {value}")

    # 2. 주요 장점
    print(f"\n{'─'*80}")
    print(f"2. 주요 장점")
    print(f"{'─'*80}")
    for name, details in risks['주요_장점'].items():
        print(f"\n  [{name.replace('_', ' ')}] (중요도: {details['중요도']})")
        print(f"    {details['설명']}")

    # 3. 주요 위험
    print(f"\n{'─'*80}")
    print(f"3. 주요 위험 요소")
    print(f"{'─'*80}")
    for risk_name, risk_data in risks['주요_위험'].items():
        print(f"\n  [{risk_name}]")
        print(f"  위험도: {risk_data['위험도']}")
        print(f"  설명: {risk_data['설명']}")

        if '영향' in risk_data:
            print(f"  영향: {risk_data['영향']}")

        if '완화_방안' in risk_data:
            print(f"  완화 방안:")
            for plan in risk_data['완화_방안']:
                print(f"    - {plan}")

    # 4. 정량적 지표
    print(f"\n{'─'*80}")
    print(f"4. 정량적 위험 지표")
    print(f"{'─'*80}")
    for metric_name, metric_data in risks['정량적_위험_지표'].items():
        print(f"\n  [{metric_name.replace('_', ' ')}]")
        for key, value in metric_data.items():
            print(f"    {key}: {value}")

    # 5. 권장 리스크 관리
    print(f"\n{'─'*80}")
    print(f"5. 권장 리스크 관리 방안")
    print(f"{'─'*80}")
    for category, items in risks['권장_리스크_관리'].items():
        print(f"\n  [{category.replace('_', ' ')}]")
        for item in items:
            print(f"    • {item}")

    # 6. AI 전략 대비 평가
    print(f"\n{'─'*80}")
    print(f"6. AI 전략 대비 비교")
    print(f"{'─'*80}")
    comparison = risks['AI_전략_대비_평가']
    print(f"\n  [AI 전략의 장점]")
    for item in comparison['AI_전략_장점']:
        print(f"    • {item}")
    print(f"\n  [대장주 전략의 장점]")
    for item in comparison['대장주_전략_장점']:
        print(f"    • {item}")
    print(f"\n  권장 사항: {comparison['권장_사항']}")
    print(f"\n  혼합 방안:")
    for key, value in comparison['혼합_방안'].items():
        print(f"    • {key}: {value}")

    # 7. 결론
    print(f"\n{'─'*80}")
    print(f"7. 결론 및 권고 사항")
    print(f"{'─'*80}")
    conclusion = risks['결론_및_권고']

    print(f"\n  [적합한 투자자]")
    for item in conclusion['적합한_투자자']:
        print(f"    ✓ {item}")

    print(f"\n  [부적합한 투자자]")
    for item in conclusion['부적합한_투자자']:
        print(f"    ✗ {item}")

    print(f"\n  [종합 평가]")
    for key, value in conclusion['종합_평가'].items():
        print(f"    {key}: {value}")

    print(f"\n  [최종 권고]")
    print(conclusion['최종_권고'])

    print(f"\n{'='*80}\n")

    return risks


def save_risk_analysis_report(output_file: str = None):
    """위험 분석 결과를 파일로 저장"""
    if output_file is None:
        output_dir = Path(__file__).parent / "reports"
        output_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = output_dir / f"sector_leader_risk_analysis_{timestamp}.md"

    risks = analyze_sector_leader_strategy_risks()

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"# 업종별 대장주 투자 전략 - 위험성 분석 보고서\n\n")
        f.write(f"**생성 일시**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"---\n\n")

        # Markdown 형식으로 작성
        f.write(f"## 1. 전략 개요\n\n")
        overview = risks['전략_개요']
        for key, value in overview.items():
            f.write(f"- **{key}**: {value}\n")

        f.write(f"\n## 2. 주요 장점\n\n")
        for name, details in risks['주요_장점'].items():
            f.write(f"### {name.replace('_', ' ')}\n")
            f.write(f"- **중요도**: {details['중요도']}\n")
            f.write(f"- **설명**: {details['설명']}\n\n")

        f.write(f"## 3. 주요 위험 요소\n\n")
        for risk_name, risk_data in risks['주요_위험'].items():
            f.write(f"### {risk_name}\n")
            f.write(f"- **위험도**: {risk_data['위험도']}\n")
            f.write(f"- **설명**: {risk_data['설명']}\n")
            if '영향' in risk_data:
                f.write(f"- **영향**: {risk_data['영향']}\n")
            if '완화_방안' in risk_data:
                f.write(f"- **완화 방안**:\n")
                for plan in risk_data['완화_방안']:
                    f.write(f"  - {plan}\n")
            f.write(f"\n")

        f.write(f"## 4. 정량적 위험 지표\n\n")
        for metric_name, metric_data in risks['정량적_위험_지표'].items():
            f.write(f"### {metric_name.replace('_', ' ')}\n")
            for key, value in metric_data.items():
                f.write(f"- **{key}**: {value}\n")
            f.write(f"\n")

        # 나머지 섹션도 동일하게...

        f.write(f"\n---\n\n")
        f.write(f"**면책 조항**: 본 분석은 교육 및 연구 목적의 참고 자료이며, 투자 권유가 아닙니다.\n")

    print(f"✅ 위험 분석 보고서 저장: {output_file}")
    return output_file


if __name__ == "__main__":
    """메인 실행"""
    import argparse

    parser = argparse.ArgumentParser(description="업종별 대장주 투자 전략")
    parser.add_argument("--action", choices=["recommend", "risk", "both"],
                       default="both", help="실행할 작업")
    parser.add_argument("--num-sectors", type=int, default=5,
                       help="선택할 업종 수")
    parser.add_argument("--leaders-per-sector", type=int, default=1,
                       help="업종당 대장주 수")
    parser.add_argument("--save-report", action="store_true",
                       help="위험 분석 보고서 저장")

    args = parser.parse_args()

    if args.action in ["recommend", "both"]:
        recommendations = get_sector_leader_recommendations(
            num_sectors=args.num_sectors,
            leaders_per_sector=args.leaders_per_sector
        )
        print(f"✅ 총 {len(recommendations)}개 종목 추천 완료\n")

    if args.action in ["risk", "both"]:
        print_risk_analysis()

        if args.save_report:
            save_risk_analysis_report()
