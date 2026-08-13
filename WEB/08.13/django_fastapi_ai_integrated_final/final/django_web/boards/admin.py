"""Django 관리자 사이트에서 게시글을 관리하기 위한 설정입니다."""
# Django admin 기능을 가져옵니다.
from django.contrib import admin
# 게시글 모델을 가져옵니다.
from .models import Board


@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    """게시글 목록/검색/필터 UI를 설정합니다."""
    # 관리자 목록에서 주요 게시글 정보를 표시합니다.
    list_display = ("id", "title", "author", "read_count", "created_at")
    # 제목, 내용, 작성자 아이디로 검색할 수 있게 합니다.
    search_fields = ("title", "content", "author__username")
    # 작성일을 기준으로 날짜 필터를 제공합니다.
    list_filter = ("created_at",)
    # 작성자 FK 선택 시 검색 UI를 제공합니다.
    autocomplete_fields = ("author",)
