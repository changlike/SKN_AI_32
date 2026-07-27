"""
FastAPI 요청과 응답의 데이터 구조를 정의합니다.
"""

# 메시지 역할의 제한된 문자열 형식을 위해 Literal을 가져옵니다.
from typing import Literal

# Pydantic 데이터 검증 클래스와 Field를 가져옵니다.
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """
    대화 내역의 단일 메시지입니다.
    """

    # 메시지 작성자 역할을 제한합니다.
    role: Literal["system", "user", "assistant"]

    # 실제 메시지 내용을 저장합니다.
    content: str = Field(min_length=1, max_length=16000)


class ChatRequest(BaseModel):
    """
    한국어 LLM 채팅 요청입니다.
    """

    # 사용자가 입력한 현재 질문입니다.
    message: str = Field(min_length=1, max_length=8000)

    # 모델 행동을 정의하는 시스템 프롬프트입니다.
    system_prompt: str = Field(
        default=(
            "당신은 정확하고 친절한 한국어 AI입니다. "
            "확실하지 않은 사실은 임의로 만들지 마세요."
        ),
        min_length=1,
        max_length=4000,
    )

    # 이전 대화 메시지 목록입니다.
    history: list[ChatMessage] = Field(default_factory=list)

    # 답변 무작위성을 조절하는 값입니다.
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)

    # 누적 확률 기반 샘플링 범위입니다.
    top_p: float = Field(default=0.9, gt=0.0, le=1.0)

    # 새로 생성할 최대 토큰 수입니다.
    max_tokens: int = Field(default=512, ge=1, le=4096)


class ChatResponse(BaseModel):
    """
    모델 답변과 서비스 성능 정보를 반환합니다.
    """

    # 실제 호출한 vLLM 모델 이름입니다.
    model: str

    # 생성된 한국어 답변입니다.
    answer: str

    # vLLM이 계산한 입력 토큰 수입니다.
    prompt_tokens: int | None = None

    # vLLM이 계산한 출력 토큰 수입니다.
    completion_tokens: int | None = None

    # 전체 토큰 수입니다.
    total_tokens: int | None = None

    # FastAPI에서 측정한 전체 응답 시간입니다.
    latency_seconds: float
