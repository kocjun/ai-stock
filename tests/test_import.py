#!/usr/bin/env python3
"""Import 테스트"""

print("Starting import test...")

try:
    print("1. Importing tools...")
    from core.tools.data_collection_tool import DataCollectionTool
    print("   ✓ DataCollectionTool imported")

    from core.tools.data_quality_tool import DataQualityTool
    print("   ✓ DataQualityTool imported")

    from core.tools.n8n_webhook_tool import N8nWebhookTool
    print("   ✓ N8nWebhookTool imported")

    print("\n2. Creating tool instances...")
    collector = DataCollectionTool()
    print("   ✓ DataCollectionTool instance created")

    quality = DataQualityTool()
    print("   ✓ DataQualityTool instance created")

    print("\n✅ All imports successful!")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
