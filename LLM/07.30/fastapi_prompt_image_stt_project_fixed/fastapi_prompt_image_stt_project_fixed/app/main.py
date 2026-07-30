"""FastAPI 애플리케이션과 정적 파일 경로를 구성합니다."""

# FastAPI 애플리케이션 클래스를 가져옵니다.
from fastapi import FastAPI

# CSS, JavaScript와 생성 파일을 제공하기 위해 StaticFiles를 가져옵니다.
from fastapi.staticfiles import StaticFiles

# 웹 페이지와 REST API 라우터를 가져옵니다.
from app.api.routes import router

# 공통 설정을 가져옵니다.
from app.core.config import settings


# 서버 시작 전에 저장 디렉터리를 생성합니다.
settings.create_directories()

# FastAPI 애플리케이션 객체를 생성합니다.
app = FastAPI(
    title=settings.app_name,
    version="2.0.0",
    description="프롬프트와 음성 STT를 Stable Diffusion 이미지 생성으로 연결합니다.",
)

# CSS와 JavaScript를 /static URL에 연결합니다.
app.mount(
    "/static",
    StaticFiles(directory=str(settings.static_dir)),
    name="static",
)

# 음성, STT 텍스트와 생성 이미지를 /storage URL에 연결합니다.
app.mount(
    "/storage",
    StaticFiles(directory=str(settings.project_root / "storage")),
    name="storage",
)

# 정의한 모든 라우터를 애플리케이션에 등록합니다.
app.include_router(router)
