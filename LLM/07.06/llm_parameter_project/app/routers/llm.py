# -*- coding: utf-8 -*-
"""LLM 실습 테스트용 API 라우터입니다."""

# FastAPI 라우터와 HTTP 오류 처리를 위해 필요한 클래스를 불러옵니다.
from fastapi import APIRouter, HTTPException

# 요청/응답 스키마를 불러옵니다.
from app.schemas import (
    BasicPromptRequest,
    DiversityRequest,
    DiversityResponse,
    LLMResponse,
    RoleChatRequest,
    TokenCompareRequest,
)

# 실제 LLM 호출 로직이 들어 있는 서비스 함수를 불러옵니다.
from app.services.llm_service_gemini import (
    gemini_basic_call,
    gemini_role_chat,
    gemini_temperature_diversity,
    gemini_token_compare,
    openai_chat,
)

# /api/llm 경로 아래에 API를 묶기 위한 라우터를 생성합니다.
router = APIRouter(prefix="/api/llm", tags=["LLM 실습 테스트"])


@router.post("/gemini/basic", response_model=LLMResponse)
def call_gemini_basic(request: BasicPromptRequest):
    """Gemini 기본 호출을 테스트합니다."""

    try:
        return gemini_basic_call(
            prompt=request.prompt,
            temperature=request.temperature,
            max_output_tokens=request.max_output_tokens,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/gemini/role", response_model=LLMResponse)
def call_gemini_role(request: RoleChatRequest):
    """시스템 지시로 Gemini의 역할과 말투를 바꾸는 테스트입니다."""

    try:
        return gemini_role_chat(
            system_instruction=request.system_instruction,
            user_message=request.user_message,
            temperature=request.temperature,
            max_output_tokens=request.max_output_tokens,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/gemini/diversity", response_model=DiversityResponse)
def check_temperature_diversity(request: DiversityRequest):
    """temperature 값에 따른 답변 다양성을 측정합니다."""

    try:
        return gemini_temperature_diversity(
            prompt=request.prompt,
            temperature=request.temperature,
            repeat_count=request.repeat_count,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/gemini/token-compare")
def compare_korean_english_tokens(request: TokenCompareRequest):
    """한국어와 영어 입력의 토큰 사용량을 비교합니다."""

    try:
        return gemini_token_compare(
            korean_text=request.korean_text,
            english_text=request.english_text,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/openai/chat", response_model=LLMResponse)
def call_openai_chat(request: RoleChatRequest):
    """OpenAI 키가 있을 때 OpenAI 호출 구조를 테스트합니다."""

    try:
        return openai_chat(
            system_instruction=request.system_instruction,
            user_message=request.user_message,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
