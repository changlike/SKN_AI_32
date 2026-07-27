"""
한국어 DPO LLM FastAPI 서비스의 메인 애플리케이션입니다.
"""

# 현재 app 디렉터리 경로를 계산하기 위해 Path를 가져옵니다.
from pathlib import Path

# FastAPI 애플리케이션과 웹 요청 객체를 가져옵니다.
from fastapi import FastAPI, Request

# CSS와 JavaScript 정적 파일 제공 기능을 가져옵니다.
from fastapi.staticfiles import StaticFiles

# Jinja2 HTML 템플릿 기능을 가져옵니다.
from fastapi.templating import Jinja2Templates

# 채팅과 시스템 API 라우터를 가져옵니다.
from app.api import chat, system

# 애플리케이션 설정을 가져옵니다.
from app.core.config import get_settings


# 현재 app 디렉터리의 절대 경로를 계산합니다.
APP_DIR = Path(__file__).resolve().parent

# 환경변수 기반 설정을 읽습니다.
settings = get_settings()

# FastAPI 애플리케이션 객체를 생성합니다.
app = FastAPI(
    title=settings.app_name,
    description=(
        "RunPod에서 DPO 파인튜닝한 한국어 모델을 "
        "vLLM으로 서빙하고 FastAPI로 제공하는 서비스입니다."
    ),
    version="1.0.0",
)

# /static URL로 CSS와 JavaScript 파일을 제공하도록 연결합니다.
app.mount(
    "/static",
    StaticFiles(directory=str(APP_DIR / "static")),
    name="static",
)

# HTML 템플릿 디렉터리를 지정합니다.
templates = Jinja2Templates(
    directory=str(APP_DIR / "templates")
)

# 채팅 API 라우터를 등록합니다.
app.include_router(chat.router)

# 시스템 상태 API 라우터를 등록합니다.
app.include_router(system.router)


@app.get("/")
def index(request: Request):
    """
    한국어 LLM 채팅 테스트 웹 화면을 반환합니다.
    """

    # index.html 템플릿에 요청 객체와 서비스 이름을 전달합니다.
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"app_name": settings.app_name},
    )
