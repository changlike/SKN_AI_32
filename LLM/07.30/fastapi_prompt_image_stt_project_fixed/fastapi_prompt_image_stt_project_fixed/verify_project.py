"""모델 다운로드 없이 프로젝트의 핵심 모듈과 주요 URL을 점검합니다."""

from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app
from app.services.image_service import run_generation_job


def main() -> None:
    """FastAPI import, 설정 이름, 첫 화면과 상태 API를 순서대로 검증합니다."""

    # 애플리케이션 객체가 정상 생성되었는지 확인합니다.
    assert app is not None

    # 백그라운드 이미지 생성 함수가 호출 가능한지 확인합니다.
    assert callable(run_generation_job)

    # 첫 화면에서 사용하는 모든 설정값이 실제로 존재하는지 확인합니다.
    assert isinstance(settings.default_inference_steps, int)
    assert isinstance(settings.default_guidance_scale, float)
    assert isinstance(settings.default_width, int)
    assert isinstance(settings.default_height, int)
    assert isinstance(settings.default_save_interval, int)

    # 실제 HTTP 요청과 동일한 방식으로 첫 화면과 상태 API를 검사합니다.
    with TestClient(app) as client:
        index_response = client.get("/")
        health_response = client.get("/api/health")

    # 첫 화면이 500 오류 없이 HTML을 반환해야 합니다.
    assert index_response.status_code == 200, index_response.text
    assert "text/html" in index_response.headers.get("content-type", "")

    # 상태 API가 정상 JSON을 반환해야 합니다.
    assert health_response.status_code == 200, health_response.text
    assert health_response.json().get("status") == "ok"

    print("[성공] FastAPI 애플리케이션 import 완료")
    print(f"[성공] 애플리케이션 이름: {app.title}")
    print("[성공] run_generation_job 함수 연결 완료")
    print("[성공] GET / 첫 화면 렌더링 완료: 200 OK")
    print("[성공] GET /api/health 상태 확인 완료: 200 OK")


if __name__ == "__main__":
    main()
