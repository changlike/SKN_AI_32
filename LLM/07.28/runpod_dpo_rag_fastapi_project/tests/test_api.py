"""FastAPI 기본 라우팅 테스트입니다."""
# 테스트 클라이언트를 가져옵니다.
from fastapi.testclient import TestClient
# 실제 앱을 가져옵니다.
from app.main import app
# 테스트 클라이언트를 생성합니다.
client = TestClient(app)

# 상태 API를 검증합니다.
def test_health():
    # 상태 API를 호출합니다.
    response = client.get('/health')
    # 정상 상태 코드를 확인합니다.
    assert response.status_code == 200
    # status 값이 ok인지 확인합니다.
    assert response.json()['status'] == 'ok'
