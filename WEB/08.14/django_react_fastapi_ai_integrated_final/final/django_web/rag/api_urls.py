from django.urls import path
from . import api_views

urlpatterns = [
    path("rag/query/", api_views.RagQueryAPIView.as_view(), name="api_rag_query"),
    path("documents/<str:filename>/", api_views.RagDocumentAPIView.as_view(), name="api_rag_document"),
    path("media/<path:asset_path>/", api_views.FastAPIMediaProxyAPIView.as_view(), name="api_ai_media"),
    path("health/", api_views.AIHealthAPIView.as_view(), name="api_ai_health"),
    path("caption/", api_views.AICaptionAPIView.as_view(), name="api_ai_caption"),
    path("generate/", api_views.AIGenerateAPIView.as_view(), name="api_ai_generate"),
    path("stt/", api_views.AISTTAPIView.as_view(), name="api_ai_stt"),
    path("tts/", api_views.AITTSAPIView.as_view(), name="api_ai_tts"),
]
