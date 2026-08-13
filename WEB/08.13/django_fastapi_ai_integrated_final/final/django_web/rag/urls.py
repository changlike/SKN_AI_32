"""Django AI 화면과 FastAPI 프록시 API URL을 연결합니다."""
# URL 패턴 선언을 위해 path를 가져옵니다.
from django.urls import path
# 같은 앱의 View 모듈을 가져옵니다.
from . import views

# 템플릿 reverse에서 사용할 앱 네임스페이스입니다.
app_name = "rag"

# 사용자가 접근할 RAG/멀티모달 화면과 내부 프록시 API 경로입니다.
urlpatterns = [
    # 기존 /rag/ 화면을 그대로 RAG 검색 페이지로 유지합니다.
    path("", views.rag_search, name="search"),
    # Django 호환용 JSON RAG API입니다.
    path("api/search/", views.rag_search_api, name="api_search"),
    # FastAPI의 PDF 원문을 Django를 통해 표시합니다.
    path("documents/<str:filename>/", views.rag_document, name="document"),
    # 멀티모달 AI 통합 화면입니다.
    path("multimodal/", views.multimodal_page, name="multimodal"),
    # FastAPI health 상태 프록시입니다.
    path("api/health/", views.ai_health, name="ai_health"),
    # 이미지 캡셔닝 프록시입니다.
    path("api/caption/", views.ai_caption, name="ai_caption"),
    # Stable Diffusion 이미지 생성 프록시입니다.
    path("api/generate/", views.ai_generate, name="ai_generate"),
    # Whisper STT 프록시입니다.
    path("api/stt/", views.ai_stt, name="ai_stt"),
    # TTS 프록시입니다.
    path("api/tts/", views.ai_tts, name="ai_tts"),
]
