"""
실제 vLLM 서버 없이 FastAPI 라우팅과 응답 형식을 검사합니다.
"""

# unittest.mock의 patch를 사용해 vLLM 호출을 모의 처리합니다.
from unittest.mock import patch

# FastAPI 애플리케이션 테스트 클라이언트를 가져옵니다.
from fastapi.testclient import TestClient

# 테스트할 FastAPI app 객체를 가져옵니다.
from app.main import app

# 모의 서비스 응답에 사용할 ChatResponse를 가져옵니다.
from app.models.schemas import ChatResponse


# 네트워크 포트를 열지 않는 테스트 클라이언트를 생성합니다.
client = TestClient(app)


def test_fastapi_health() -> None:
    """
    FastAPI 자체 상태 API가 정상 응답하는지 확인합니다.
    """

    # 상태 확인 API를 호출합니다.
    response = client.get("/api/system/health")

    # HTTP 200 성공인지 검사합니다.
    assert response.status_code == 200

    # 응답 JSON을 읽습니다.
    data = response.json()

    # 상태가 ok인지 검사합니다.
    assert data["status"] == "ok"

    # 모델 이름 설정이 포함되어 있는지 검사합니다.
    assert "vllm_model_name" in data


@patch("app.api.chat.vllm_service.chat")
def test_chat(mock_chat) -> None:
    """
    vLLM 호출을 모의 처리하여 채팅 API 형식을 검사합니다.
    """

    # 모의 vLLM 서비스 반환값을 설정합니다.
    mock_chat.return_value = ChatResponse(
        model="korean-dpo-model",
        answer="배송 지연으로 불편을 드려 죄송합니다.",
        prompt_tokens=20,
        completion_tokens=10,
        total_tokens=30,
        latency_seconds=0.5,
    )

    # 채팅 API에 테스트 요청을 보냅니다.
    response = client.post(
        "/api/chat",
        json={
            "message": "배송이 늦어요.",
            "system_prompt": "친절한 한국어 상담 AI입니다.",
            "history": [],
            "temperature": 0.2,
            "top_p": 0.9,
            "max_tokens": 128,
        },
    )

    # API가 정상 성공했는지 검사합니다.
    assert response.status_code == 200

    # 응답 JSON을 읽습니다.
    data = response.json()

    # 모의 모델 이름이 반환되는지 검사합니다.
    assert data["model"] == "korean-dpo-model"

    # 답변이 빈 문자열이 아닌지 검사합니다.
    assert data["answer"]
