"""RAG 앱 URL 설정입니다."""
from django.urls import path
from . import views

app_name = "rag"

urlpatterns = [
    path("", views.rag_search, name="search"),
    path("api/search/", views.rag_search_api, name="api_search"),
    path("documents/<str:filename>/", views.rag_document, name="document"),
]
