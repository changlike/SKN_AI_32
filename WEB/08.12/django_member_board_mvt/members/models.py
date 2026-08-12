"""Spring MVC의 Member DTO/테이블을 Django 사용자 모델로 변환한 파일입니다."""
# Django가 제공하는 확장 가능한 기본 사용자 모델 AbstractUser를 가져옵니다.
from django.contrib.auth.models import AbstractUser
# 데이터베이스 필드를 선언하기 위한 models 모듈을 가져옵니다.
from django.db import models


class Member(AbstractUser):
    """회원가입, 인증, 세션, 관리자 권한을 함께 처리하는 사용자 정의 회원 모델입니다."""
    # 성별 선택값을 상수로 정의하여 DB에는 짧은 값, 화면에는 한글 설명을 사용합니다.
    GENDER_CHOICES = [("M", "남성"), ("F", "여성"), ("N", "선택 안 함")]
    # 가입방식 선택값을 정의합니다. 이번 프로젝트의 일반 회원가입은 direct를 사용합니다.
    SIGN_TYPE_CHOICES = [("direct", "직접 가입"), ("kakao", "카카오"), ("naver", "네이버"), ("google", "구글")]

    # AbstractUser.username 필드를 USERID처럼 사용하며 최대 길이를 원본 프로젝트보다 넉넉한 50자로 확장합니다.
    username = models.CharField("회원 아이디", max_length=50, unique=True)
    # 원본 Member.userName에 대응하는 화면 표시용 이름입니다.
    display_name = models.CharField("회원 이름", max_length=30)
    # 원본 Member.gender에 대응하며 미선택 값도 허용합니다.
    gender = models.CharField("성별", max_length=1, choices=GENDER_CHOICES, default="N")
    # 원본 Member.age에 대응하며 입력하지 않을 수도 있도록 null/blank를 허용합니다.
    age = models.PositiveIntegerField("나이", null=True, blank=True)
    # 원본 Member.phone에 대응하는 전화번호 문자열 필드입니다.
    phone = models.CharField("전화번호", max_length=20, blank=True)
    # AbstractUser.email을 재선언해 이메일 입력을 필수값으로 설정합니다.
    email = models.EmailField("이메일", unique=True)
    # 원본 SIGNTYPE 필드에 대응합니다.
    sign_type = models.CharField("가입 방식", max_length=10, choices=SIGN_TYPE_CHOICES, default="direct")
    # 원본 PHOTO_FILENAME에 대응하며 실제 파일을 media/member_photos/에 저장합니다.
    photo = models.ImageField("프로필 사진", upload_to="member_photos/%Y/%m/", blank=True, null=True)
    # 원본 LASTMODIFIED 역할을 하는 마지막 회원정보 수정 시각입니다.
    updated_at = models.DateTimeField("마지막 수정일", auto_now=True)

    class Meta:
        # Django 관리자 화면과 디버깅 시 표시할 단수 모델 이름입니다.
        verbose_name = "회원"
        # 복수 모델 이름입니다.
        verbose_name_plural = "회원"
        # 회원 목록 기본 정렬을 최근 가입 순으로 지정합니다.
        ordering = ["-date_joined"]

    def __str__(self):
        """관리자 화면 등에서 회원 객체를 읽기 쉽게 표시합니다."""
        # 아이디와 회원 이름을 함께 문자열로 반환합니다.
        return f"{self.username} ({self.display_name})"

    @property
    def admin_yn(self):
        """원본 프로젝트의 ADMIN_YN 값을 Django 권한 필드에 맞춰 표현합니다."""
        # staff 또는 superuser이면 관리자 Y, 아니면 N을 반환합니다.
        return "Y" if self.is_staff or self.is_superuser else "N"

    @property
    def login_ok(self):
        """원본 프로젝트의 LOGIN_OK 값을 Django is_active와 대응시킵니다."""
        # 활성 사용자이면 Y, 로그인 제한 사용자이면 N을 반환합니다.
        return "Y" if self.is_active else "N"
