"""
FastAPI 자체 상태와 vLLM 연결 상태를 확인합니다.
"""

# FastAPI 라우터와 HTTP 예외를 가져옵니다.
from fastapi import APIRouter, HTTPException

# OpenAI 호환 클라이언트 오류를 가져옵니다.
from openai import OpenAIError

# 애플리케이션 설정을 가져옵니다.
from app.core.config import get_settings

# vLLM 서비스 객체를 가져옵니다.
from app.services.vllm_service import vllm_service


# 시스템 확인 API 라우터를 생성합니다.
router = APIRouter(prefix="/api/system", tags=["system"])


@router.get("/health")
def health() -> dict:
    """
    FastAPI 프로세스 자체의 정상 상태를 반환합니다.
    """

    # 현재 설정을 읽습니다.
    settings = get_settings()

    # 서비스 상태와 연결 대상 정보를 반환합니다.
    return {
        "status": "ok",
        "app_name": settings.app_name,
        "vllm_base_url": settings.vllm_base_url,
        "vllm_model_name": settings.vllm_model_name,
    }


@router.get("/vllm-health")
def vllm_health() -> dict:
    """
    vLLM 모델 목록 API를 호출해 실제 연결 상태를 확인합니다.
    """

    try:
        # vLLM 서비스의 상태 확인 결과를 반환합니다.
        return vllm_service.health()
    except OpenAIError as error:
        # vLLM 서버가 꺼졌거나 인증에 실패하면 502로 반환합니다.
        raise HTTPException(
            status_code=502,
            detail=f"vLLM 상태 확인 실패: {error}",
        ) from error
