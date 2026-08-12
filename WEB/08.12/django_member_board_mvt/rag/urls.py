"""RAG 앱의 VIEW의 URL 설정 스크립트"""
from .import views
from django.urls import path

app_name = 'rag'

urlpatterns = [
    path("", views.rag_search, name="search"),
    path("api/search", views.rag_search_api, name="api_search")
]