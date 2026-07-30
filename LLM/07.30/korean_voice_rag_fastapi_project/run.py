"""PyCharm 실행 버튼으로 FastAPI 서버를 시작합니다."""
import uvicorn  # ASGI 서버 실행 패키지를 가져옵니다.
from app.config import settings  # 호스트와 포트 설정을 가져옵니다.
if __name__ == '__main__':  # 직접 실행된 경우에만 서버를 시작합니다.
    uvicorn.run('app.main:app', host=settings.HOST, port=settings.PORT, reload=True)  # 개발용 자동 재시작 서버를 실행합니다.
