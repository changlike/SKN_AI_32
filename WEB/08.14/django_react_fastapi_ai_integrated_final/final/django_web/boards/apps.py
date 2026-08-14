# Django 앱 설정 기반 클래스를 가져옵니다.
from django.apps import AppConfig


class BoardsConfig(AppConfig):
    """게시판 앱의 기본 설정입니다."""
    # 자동 PK 필드 타입을 지정합니다.
    default_auto_field = "django.db.models.BigAutoField"
    # 앱 패키지 이름을 지정합니다.
    name = "boards"
