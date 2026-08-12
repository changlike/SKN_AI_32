"""Django 관리자 사이트에서 회원 모델을 관리하기 위한 설정입니다."""
# 관리자 사이트 등록 기능을 가져옵니다.
from django.contrib import admin
# AbstractUser 기반 모델에 맞는 관리자 UI 클래스를 가져옵니다.
from django.contrib.auth.admin import UserAdmin
# 사용자 정의 회원 모델을 가져옵니다.
from .models import Member


@admin.register(Member)
class MemberAdmin(UserAdmin):
    """기본 UserAdmin에 프로젝트 회원 필드를 추가합니다."""
    # 관리자 목록 화면에서 빠르게 확인할 필드를 지정합니다.
    list_display = ("username", "display_name", "email", "is_active", "is_staff", "date_joined")
    # 아이디, 이름, 이메일로 검색할 수 있게 합니다.
    search_fields = ("username", "display_name", "email")
    # 로그인 허용 여부와 관리자 여부로 필터링할 수 있게 합니다.
    list_filter = ("is_active", "is_staff", "is_superuser", "sign_type")
    # 기존 UserAdmin 수정 화면의 필드 그룹 뒤에 프로젝트 전용 필드를 추가합니다.
    fieldsets = UserAdmin.fieldsets + (("추가 회원 정보", {"fields": ("display_name", "gender", "age", "phone", "sign_type", "photo", "updated_at")}),)
    # updated_at은 자동 생성 필드이므로 읽기 전용으로 표시합니다.
    readonly_fields = ("updated_at",)
    # 관리자 화면에서 새 사용자를 만들 때 프로젝트 필드를 추가 입력할 수 있게 합니다.
    add_fieldsets = UserAdmin.add_fieldsets + (("추가 회원 정보", {"fields": ("display_name", "email", "gender", "age", "phone")}),)
