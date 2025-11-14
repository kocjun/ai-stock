"""
레드팀 검증 시스템

로컬 LLM 결과를 OpenAI로 검증 및 교정
"""
import sys
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from paper_trading.trading_crew import run_daily_trading_workflow
from core.tools.n8n_webhook_tool import N8nWebhookTool


def run_redteam_validation(account_id: int = 1,
                           market: str = "KOSPI",
                           limit: int = 20,
                           top_n: int = 10) -> Dict:
    """
    레드팀 검증 실행

    1. 로컬 LLM으로 실행 (메인)
    2. OpenAI로 동일 작업 실행 (레드팀)
    3. 결과 비교 및 차이 분석
    4. 교정 레포트 생성

    Args:
        account_id: 계좌 ID
        market: 시장
        limit: 분석 종목 수
        top_n: 선정 종목 수

    Returns:
        검증 레포트
    """

    print("="*80)
    print("🔴 레드팀 검증 시작")
    print("="*80)

    # Step 1: 로컬 LLM 실행
    print("\n[1/3] 로컬 LLM (메인) 실행 중...")
    print("-"*60)
    os.environ["LLM_MODE"] = "main"

    try:
        local_result = run_daily_trading_workflow(
            account_id=account_id,
            market=market,
            limit=limit,
            top_n=top_n,
            execute_trades=False  # 검증 모드는 실제 거래 X
        )
        local_status = "success"
    except Exception as e:
        print(f"❌ 로컬 LLM 실행 실패: {e}")
        local_result = {"error": str(e)}
        local_status = "failed"

    # Step 2: OpenAI 레드팀 실행
    print("\n[2/3] OpenAI 레드팀 실행 중...")
    print("-"*60)
    os.environ["LLM_MODE"] = "redteam"

    try:
        redteam_result = run_daily_trading_workflow(
            account_id=account_id,
            market=market,
            limit=limit,
            top_n=top_n,
            execute_trades=False
        )
        redteam_status = "success"
    except Exception as e:
        print(f"❌ 레드팀 LLM 실행 실패: {e}")
        redteam_result = {"error": str(e)}
        redteam_status = "failed"

    # LLM_MODE 원복
    os.environ["LLM_MODE"] = "main"

    # Step 3: 결과 비교
    print("\n[3/3] 결과 비교 분석 중...")
    print("-"*60)

    if local_status == "success" and redteam_status == "success":
        comparison = compare_results(local_result, redteam_result)
    else:
        comparison = {
            'status': 'incomplete',
            'local_status': local_status,
            'redteam_status': redteam_status,
            'message': '한 쪽 또는 양쪽 실행이 실패했습니다'
        }

    # 레포트 생성
    report = generate_validation_report(
        local_result,
        redteam_result,
        comparison,
        local_status,
        redteam_status
    )

    # 저장
    save_validation_report(report)

    # n8n 알림
    send_validation_alert(report)

    return report


def compare_results(local: Dict, redteam: Dict) -> Dict:
    """
    두 결과를 비교

    Args:
        local: 로컬 LLM 결과
        redteam: OpenAI 레드팀 결과

    Returns:
        비교 결과
    """
    # AI 분석 단계의 추천 종목 추출
    local_recs = local.get('steps', {}).get('ai_analysis', {}).get('recommendations', [])
    redteam_recs = redteam.get('steps', {}).get('ai_analysis', {}).get('recommendations', [])

    # 종목 코드 집합
    local_codes = {r['code'] for r in local_recs if isinstance(r, dict) and 'code' in r}
    redteam_codes = {r['code'] for r in redteam_recs if isinstance(r, dict) and 'code' in r}

    # 일치하는 종목
    agreed_codes = local_codes & redteam_codes
    agreement_count = len(agreed_codes)

    # 일치율 계산
    if len(redteam_codes) > 0:
        agreement_rate = agreement_count / len(redteam_codes)
    else:
        agreement_rate = 0

    # 차이점
    local_only = local_codes - redteam_codes
    redteam_only = redteam_codes - local_codes

    return {
        'agreement_count': agreement_count,
        'agreement_rate': agreement_rate,
        'agreed_stocks': list(agreed_codes),
        'local_only_stocks': list(local_only),
        'redteam_only_stocks': list(redteam_only),
        'local_total': len(local_codes),
        'redteam_total': len(redteam_codes),
        'recommendation': get_recommendation(agreement_rate)
    }


def get_recommendation(agreement_rate: float) -> str:
    """
    일치율에 따른 권장사항

    Args:
        agreement_rate: 일치율 (0-1)

    Returns:
        권장사항 메시지
    """
    if agreement_rate >= 0.8:
        return "✅ 로컬 LLM 분석이 신뢰할 수 있습니다."
    elif agreement_rate >= 0.5:
        return "⚠️ 로컬 LLM 분석을 참고하되, 레드팀 결과를 검토하세요."
    else:
        return "❌ 로컬 LLM 분석 품질이 낮습니다. OpenAI 결과를 사용하세요."


def generate_validation_report(local: Dict,
                               redteam: Dict,
                               comparison: Dict,
                               local_status: str,
                               redteam_status: str) -> Dict:
    """
    검증 레포트 생성

    Args:
        local: 로컬 결과
        redteam: 레드팀 결과
        comparison: 비교 결과
        local_status: 로컬 실행 상태
        redteam_status: 레드팀 실행 상태

    Returns:
        레포트
    """
    report = {
        'timestamp': datetime.now().isoformat(),
        'status': {
            'local': local_status,
            'redteam': redteam_status
        }
    }

    # 성공 시에만 비교 결과 추가
    if local_status == "success" and redteam_status == "success":
        local_recs = local.get('steps', {}).get('ai_analysis', {}).get('recommendations', [])
        redteam_recs = redteam.get('steps', {}).get('ai_analysis', {}).get('recommendations', [])

        report['summary'] = {
            'agreement_rate': f"{comparison['agreement_rate']*100:.1f}%",
            'recommendation': comparison['recommendation']
        }

        report['local_llm'] = {
            'model': os.getenv('OPENAI_MODEL_NAME', 'gpt-oss:120b'),
            'recommendations_count': len(local_recs),
            'recommendations': local_recs[:10] if local_recs else []  # 최대 10개만
        }

        report['redteam_llm'] = {
            'model': os.getenv('REDTEAM_MODEL', 'gpt-4o-mini'),
            'recommendations_count': len(redteam_recs),
            'recommendations': redteam_recs[:10] if redteam_recs else []
        }

        report['comparison'] = comparison
    else:
        report['error'] = {
            'local': local.get('error', 'No error') if local_status == "failed" else None,
            'redteam': redteam.get('error', 'No error') if redteam_status == "failed" else None
        }

    return report


def save_validation_report(report: Dict):
    """
    레포트 저장

    Args:
        report: 검증 레포트
    """
    log_dir = Path(__file__).parent / "logs" / "redteam"
    log_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = log_dir / f"validation_{timestamp}.json"

    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\n📝 검증 레포트 저장: {log_file}")


def send_validation_alert(report: Dict):
    """
    n8n으로 알림 전송

    Args:
        report: 검증 레포트
    """
    webhook_url = os.getenv("N8N_WEBHOOK_URL")
    if not webhook_url:
        print("⚠️ N8N_WEBHOOK_URL이 설정되지 않아 알림을 전송하지 않습니다.")
        return

    webhook = N8nWebhookTool(webhook_url)

    # 성공 시 메시지
    if report['status']['local'] == "success" and report['status']['redteam'] == "success":
        message = f"""
🔴 레드팀 검증 결과

일치율: {report['summary']['agreement_rate']}
{report['summary']['recommendation']}

로컬 LLM: {report['local_llm']['model']}
추천 종목 수: {report['local_llm']['recommendations_count']}

레드팀 LLM: {report['redteam_llm']['model']}
추천 종목 수: {report['redteam_llm']['recommendations_count']}

일치하는 종목 ({report['comparison']['agreement_count']}개):
{', '.join(report['comparison']['agreed_stocks']) if report['comparison']['agreed_stocks'] else '없음'}

로컬만 추천 ({len(report['comparison']['local_only_stocks'])}개):
{', '.join(report['comparison']['local_only_stocks']) if report['comparison']['local_only_stocks'] else '없음'}

레드팀만 추천 ({len(report['comparison']['redteam_only_stocks'])}개):
{', '.join(report['comparison']['redteam_only_stocks']) if report['comparison']['redteam_only_stocks'] else '없음'}
        """
    else:
        # 실패 시 메시지
        message = f"""
🔴 레드팀 검증 오류

로컬 LLM 상태: {report['status']['local']}
레드팀 LLM 상태: {report['status']['redteam']}

오류 내용을 확인해주세요.
        """

    try:
        webhook.send_alert("레드팀 검증 완료", message)
        print("✅ n8n 알림 전송 완료")
    except Exception as e:
        print(f"⚠️ n8n 알림 전송 실패: {e}")


if __name__ == "__main__":
    """메인 실행"""
    import argparse

    parser = argparse.ArgumentParser(description="레드팀 검증 시스템")
    parser.add_argument("--account-id", type=int, default=1, help="계좌 ID")
    parser.add_argument("--market", default="KOSPI", choices=["KOSPI", "KOSDAQ"], help="시장")
    parser.add_argument("--limit", type=int, default=20, help="분석 종목 수")
    parser.add_argument("--top-n", type=int, default=10, help="선정 종목 수")

    args = parser.parse_args()

    try:
        report = run_redteam_validation(
            account_id=args.account_id,
            market=args.market,
            limit=args.limit,
            top_n=args.top_n
        )

        print("\n" + "="*80)
        print("🔴 레드팀 검증 완료")
        print("="*80)

        if report['status']['local'] == "success" and report['status']['redteam'] == "success":
            print(f"\n일치율: {report['summary']['agreement_rate']}")
            print(f"{report['summary']['recommendation']}")
            print(f"\n로컬 추천: {report['local_llm']['recommendations_count']}개")
            print(f"레드팀 추천: {report['redteam_llm']['recommendations_count']}개")
            print(f"일치: {report['comparison']['agreement_count']}개")
        else:
            print("\n⚠️ 검증 실행 중 오류가 발생했습니다.")
            print("로그 파일을 확인해주세요.")

    except Exception as e:
        print(f"\n❌ 레드팀 검증 오류: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
