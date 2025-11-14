"""n8n Webhook 통합 Tool"""

from typing import Any
from crewai.tools import BaseTool
import requests
import json
from datetime import datetime


class N8nWebhookTool(BaseTool):
    name: str = "n8n_webhook_notifier"
    description: str = """
    n8n 워크플로에 결과를 전송합니다.

    JSON 형태의 데이터를 n8n webhook으로 전송하여
    후속 자동화 프로세스를 트리거합니다.
    """

    webhook_url: str = ""

    def __init__(self, webhook_url: str):
        super().__init__()
        self.webhook_url = webhook_url

    def _run(self, result: Any) -> str:
        """n8n webhook으로 결과 전송"""
        if not self.webhook_url:
            return "⚠ n8n webhook URL이 설정되지 않았습니다."

        try:
            # 결과를 JSON 직렬화 가능한 형태로 변환
            if isinstance(result, str):
                payload = {
                    "timestamp": datetime.now().isoformat(),
                    "message": result,
                    "type": "text"
                }
            elif isinstance(result, dict):
                payload = {
                    "timestamp": datetime.now().isoformat(),
                    **result
                }
            else:
                payload = {
                    "timestamp": datetime.now().isoformat(),
                    "result": str(result),
                    "type": "unknown"
                }

            # n8n webhook 호출
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=15,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()

            return f"✓ n8n webhook 호출 성공 (status: {response.status_code})"

        except requests.exceptions.Timeout:
            return "✗ n8n webhook 호출 타임아웃 (15초 초과)"
        except requests.exceptions.ConnectionError:
            return f"✗ n8n 연결 실패: {self.webhook_url} 접근 불가"
        except requests.exceptions.HTTPError as e:
            return f"✗ n8n webhook HTTP 오류: {e.response.status_code}"
        except Exception as e:
            return f"✗ n8n webhook 호출 실패: {str(e)}"
