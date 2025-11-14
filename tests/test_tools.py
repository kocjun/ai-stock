"""커스텀 도구 테스트 스크립트"""

from tools.data_collection_tool import DataCollectionTool
from tools.data_quality_tool import DataQualityTool
from tools.n8n_webhook_tool import N8nWebhookTool
import os
from dotenv import load_dotenv

load_dotenv()

print("=" * 70)
print("CrewAI 커스텀 도구 테스트")
print("=" * 70)

# 1. DataCollectionTool 테스트
print("\n[1] DataCollectionTool 테스트")
print("-" * 70)
collector = DataCollectionTool()

print("\n1-1. 종목 리스트 수집 (코스피 10개)")
result = collector._run("collect_stocks KOSPI 10")
print(result)

print("\n1-2. 단일 종목 가격 수집 (삼성전자 7일)")
result = collector._run("collect_prices 005930 7")
print(result)

# 2. DataQualityTool 테스트
print("\n\n[2] DataQualityTool 테스트")
print("-" * 70)
quality_checker = DataQualityTool()

print("\n2-1. 전체 품질 체크")
result = quality_checker._run("check_all")
print(result)

# 3. N8nWebhookTool 테스트
print("\n\n[3] N8nWebhookTool 테스트")
print("-" * 70)
webhook_url = os.getenv("N8N_WEBHOOK_URL")
if webhook_url:
    webhook = N8nWebhookTool(webhook_url=webhook_url)
    result = webhook._run({
        "type": "test",
        "message": "도구 테스트 성공",
        "test_timestamp": "2025-10-12"
    })
    print(result)
else:
    print("⚠ N8N_WEBHOOK_URL이 설정되지 않았습니다.")

print("\n" + "=" * 70)
print("테스트 완료")
print("=" * 70)
