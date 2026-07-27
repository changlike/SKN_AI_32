"""
OpenAI Python 클라이언트를 사용해 vLLM OpenAI 호환 서버를 호출합니다.
"""

# 요청 전체 시간을 측정하기 위해 time을 가져옵니다.
import time

# OpenAI 호환 API 클라이언트를 가져옵니다.
from openai import OpenAI

# 서비스 설정을 가져옵니다.
from app.core.config import Settings, get_settings

# 요청과 응답 스키마를 가져옵니다.
from app.models.schemas import ChatRequest, ChatResponse


class VLLMService:
    """
    FastAPI와 vLLM 사이의 추론 호출을 담당합니다.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        """
        vLLM 주소와 API 키를 사용하는 OpenAI 클라이언트를 생성합니다.
        """

        # 외부 설정이 없으면 애플리케이션 공용 설정을 사용합니다.
        self.settings = settings or get_settings()

        # vLLM의 OpenAI 호환 /v1 주소를 사용하는 클라이언트를 생성합니다.
        self.client = OpenAI(
            base_url=self.settings.vllm_base_url,
            api_key=self.settings.vllm_api_key,
            timeout=120.0,
            max_retries=1,
        )

    def health(self) -> dict:
        """
        vLLM 서버의 모델 목록을 조회하여 연결 상태를 확인합니다.
        """

        # vLLM의 /v1/models API를 호출합니다.
        models = self.client.models.list()

        # 반환된 모델 ID를 문자열 목록으로 변환합니다.
        model_ids = [model.id for model in models.data]

        # 연결 결과를 딕셔너리로 반환합니다.
        return {
            "status": "ok",
            "base_url": self.settings.vllm_base_url,
            "models": model_ids,
        }

    def chat(self, request: ChatRequest) -> ChatResponse:
        """
        시스템 프롬프트, 대화 이력, 현재 질문으로 답변을 생성합니다.
        """

        # vLLM에 전달할 메시지 목록을 시스템 메시지로 시작합니다.
        messages: list[dict[str, str]] = [
            {
                "role": "system",
                "content": request.system_prompt,
            }
        ]

        # 이전 대화 이력을 순서대로 추가합니다.
        for message in request.history:
            messages.append(
                {
                    "role": message.role,
                    "content": message.content,
                }
            )

        # 현재 사용자 질문을 마지막 메시지로 추가합니다.
        messages.append(
            {
                "role": "user",
                "content": request.message,
            }
        )

        # 전체 API 지연 시간 측정을 시작합니다.
        started_at = time.perf_counter()

        # vLLM의 OpenAI 호환 Chat Completions API를 호출합니다.
        completion = self.client.chat.completions.create(
            model=self.settings.vllm_model_name,
            messages=messages,
            temperature=request.temperature,
            top_p=request.top_p,
            max_tokens=request.max_tokens,
        )

        # 전체 응답 시간을 계산합니다.
        latency = time.perf_counter() - started_at

        # 첫 번째 선택지의 메시지 내용을 가져옵니다.
        answer = completion.choices[0].message.content or ""

        # 토큰 사용 정보가 존재할 수 있으므로 별도 변수에 저장합니다.
        usage = completion.usage

        # 구조화된 FastAPI 응답 객체를 반환합니다.
        return ChatResponse(
            model=completion.model,
            answer=answer.strip(),
            prompt_tokens=usage.prompt_tokens if usage else None,
            completion_tokens=usage.completion_tokens if usage else None,
            total_tokens=usage.total_tokens if usage else None,
            latency_seconds=latency,
        )


# 애플리케이션에서 공유할 vLLM 서비스 객체를 생성합니다.
vllm_service = VLLMService()
