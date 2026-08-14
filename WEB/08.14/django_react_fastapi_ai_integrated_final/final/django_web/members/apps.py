# Django 앱 설정 기반 클래스를 가져옵니다.
from django.apps import AppConfig


class MembersConfig(AppConfig):
    """회원 앱의 기본 설정을 정의합니다."""
    # 기본 PK 타입을 BigAutoField로 지정합니다.
    default_auto_field = "django.db.models.BigAutoField"
    # INSTALLED_APPS에서 사용할 앱 패키지 이름입니다.
    name = "members"
