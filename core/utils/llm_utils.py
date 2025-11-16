"""
LLM 클라이언트 통합 관리

메인: Ollama 로컬 LLM (무료)
검증: OpenAI API (레드팀)
"""
from crewai import LLM
import os
from dotenv import load_dotenv
import requests

load_dotenv()


def build_llm(mode: str = None) -> LLM:
    """
    LLM 클라이언트 생성

    Args:
        mode: 'main' (로컬) 또는 'redteam' (OpenAI 검증)
              None이면 환경변수 LLM_MODE 사용

    Returns:
        LLM 객체
    """
    if mode is None:
        mode = get_llm_mode()

    if mode == "redteam":
        # OpenAI 레드팀 검증용
        model_name = os.getenv("REDTEAM_MODEL", "gpt-4o-mini")
        return LLM(
            model=model_name,
            api_key=os.getenv("OPENAI_API_KEY")
        )

    else:
        # Ollama 로컬 메인
        base_url = os.getenv("OPENAI_API_BASE", "http://127.0.0.1:11434")
        model_name = _select_ollama_model(base_url)

        # ollama/ prefix 자동 추가
        if not model_name.startswith("ollama/"):
            model_name = f"ollama/{model_name}"

        return LLM(
            model=model_name,
            base_url=base_url,
            api_key="ollama"
        )


def get_llm_mode() -> str:
    """
    현재 LLM 모드 반환

    Returns:
        'main' (로컬) 또는 'redteam' (OpenAI)
    """
    return os.getenv("LLM_MODE", "main")


def get_current_model_info() -> dict:
    """
    현재 사용 중인 LLM 정보 반환

    Returns:
        dict: 모델 정보
    """
    mode = get_llm_mode()

    if mode == "redteam":
        return {
            "mode": "redteam",
            "provider": "OpenAI",
            "model": os.getenv("REDTEAM_MODEL", "gpt-4o-mini"),
            "cost": "유료 (사용량 기반)"
        }
    else:
        return {
            "mode": "main",
            "provider": "Ollama",
            "model": os.getenv("OPENAI_MODEL_NAME", "gpt-oss:120b"),
            "cost": "무료 (로컬)"
        }


def _get_candidate_models() -> list[str]:
    primary = os.getenv("OPENAI_MODEL_NAME", "gpt-oss:120b")
    fallback = os.getenv("OPENAI_MODEL_FALLBACK")
    candidates = [primary]
    if fallback:
        fallback = fallback.strip()
        if fallback and fallback not in candidates:
            candidates.append(fallback)
    return candidates


def _ollama_model_available(base_url: str, model_name: str, timeout: float) -> bool:
    """Ollama 서버에서 특정 모델이 준비됐는지 확인."""
    url = base_url.rstrip("/") + "/api/tags"
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        payload = resp.json()
        names = {
            str(m.get("name") or m.get("model") or "").strip()
            for m in payload.get("models", [])
        }
        target = model_name.replace("ollama/", "")
        return target in names or model_name in names
    except Exception as exc:
        print(f"[LLM] Ollama healthcheck failed for {model_name}: {exc}")
        return False


def _select_ollama_model(base_url: str) -> str:
    """
    기본 모델을 우선 사용하되, 준비되지 않았으면 fallback 모델 사용.
    """
    timeout = float(os.getenv("LLM_HEALTHCHECK_TIMEOUT", "5"))
    candidates = _get_candidate_models()

    for idx, candidate in enumerate(candidates):
        if _ollama_model_available(base_url, candidate, timeout):
            if idx > 0:
                print(f"[LLM] Primary model unavailable. Falling back to {candidate}.")
            return candidate

    print("[LLM] Unable to verify Ollama models via healthcheck; "
          "using primary configuration.")
    return candidates[0]


if __name__ == "__main__":
    """테스트 및 정보 출력"""
    print("="*60)
    print("LLM 설정 정보")
    print("="*60)

    info = get_current_model_info()
    print(f"\n모드: {info['mode']}")
    print(f"프로바이더: {info['provider']}")
    print(f"모델: {info['model']}")
    print(f"비용: {info['cost']}")

    print("\n" + "="*60)
    print("LLM 객체 생성 테스트")
    print("="*60)

    try:
        llm = build_llm()
        print(f"\n✅ LLM 객체 생성 성공")
        print(f"   모델: {llm.model}")
    except Exception as e:
        print(f"\n❌ LLM 객체 생성 실패: {e}")
