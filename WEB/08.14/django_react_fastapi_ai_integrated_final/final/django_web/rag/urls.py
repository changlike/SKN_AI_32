"""Django AI 화면과 FastAPI 프록시 API URL을 클래스 기반 View에 연결합니다."""
# URL 패턴 선언을 위해 path를 가져옵니다.
from django.urls import path
# 같은 앱의 View 모듈을 가져옵니다.
from . import views

# 템플릿 reverse에서 사용할 앱 네임스페이스입니다.
app_name = "rag"

# 기존 URL 경로와 name은 그대로 유지하고 View 연결만 as_view() 방식으로 변경합니다.
urlpatterns = [
    path("", views.RagSearchView.as_view(), name="search"),
    path("api/search/", views.RagSearchAPIView.as_view(), name="api_search"),
    path("documents/<str:filename>/", views.RagDocumentView.as_view(), name="document"),
    path("multimodal/", views.MultimodalPageView.as_view(), name="multimodal"),
    path("api/health/", views.AIHealthView.as_view(), name="ai_health"),
    path("api/caption/", views.AICaptionView.as_view(), name="ai_caption"),
    path("api/generate/", views.AIGenerateView.as_view(), name="ai_generate"),
    path("api/stt/", views.AISTTView.as_view(), name="ai_stt"),
    path("api/tts/", views.AITTSView.as_view(), name="ai_tts"),
]
