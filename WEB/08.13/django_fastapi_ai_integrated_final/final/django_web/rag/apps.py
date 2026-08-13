"""OpenAI + ChromaDB 기반 RAG 검색 앱 설정입니다."""
from django.apps import AppConfig


class RagConfig(AppConfig):
    """문서와 게시글을 벡터 검색하는 RAG 앱입니다."""
    default_auto_field = "django.db.models.BigAutoField"
    name = "rag"
    verbose_name = "RAG 검색"
