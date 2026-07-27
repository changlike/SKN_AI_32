"""
한국어 채팅 요청을 처리하는 API 라우터입니다.
"""

# FastAPI 라우터와 HTTP 예외를 가져옵니다.
from fastapi import APIRouter, HTTPException

# OpenAI 호환 클라이언트 오류의 공통 부모 클래스를 가져옵니다.
from openai import OpenAIError

# 채팅 요청과 응답 스키마를 가져옵니다.
from app.models.schemas import ChatRequest, ChatResponse

# vLLM 호출 서비스 객체를 가져옵니다.
from app.services.vllm_service import vllm_service


# /api 경로에서 사용할 라우터를 생성합니다.
router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    """
    FastAPI를 통해 vLLM 한국어 모델의 답변을 생성합니다.
    """

    try:
        # vLLM 서비스에 채팅 요청을 전달하고 결과를 반환합니다.
        return vllm_service.chat(request)
    except OpenAIError as error:
        # vLLM 연결 또는 응답 오류를 502 Bad Gateway로 변환합니다.
        raise HTTPException(
            status_code=502,
            detail=f"vLLM 호출 실패: {error}",
        ) from error
