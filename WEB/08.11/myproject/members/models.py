# Django 기본 사용자 모델을 확장하기 위해 가져옴
from django.contrib.auth.models import AbstractUser

# Model 과 DB 필드(테이블의 컬럼)를 정의하기 위함
from django.db import models

# AbstractUser 를 상속받아서, Django 인증 기능을 그대로 사용함
class Member(AbstractUser):
    # 성별 선택값
    GENDER_CHOICES = [
        ('M', '남성'),
        ('F', '여성'),
        ('N', '선택 안 함'),
    ]

    # 로그인할 아이디
    username = models.CharField(
        "회원 아이디",
        max_length=50,
        unique=True,
    )

    # 화면에 보여줄 실제 회원 이름
    display_name = models.CharField(
        "회원 이름",
        max_length=30,
    )

    # 성별
    gender = models.CharField(
        "성별",
        max_length=1,
        choices=GENDER_CHOICES,
        default='N')

    # 나이
    age = models.PositiveIntegerField(
        "나이",
        null=True,
        blank=True,
    )

    # 전화번호
    phone = models.CharField(
        "전화번호",
        max_length=20,
        blank=True,
    )

    # 이메일
    email = models.EmailField(
        "이메일",
        unique=True,
    )

    # 프로필 사진
    photo = models.ImageField(
        "프로필 사진",
        upload_to='member_photos/%Y/%m/',
        blank=True,
        null=True,
    )

    # 내 정보 수정 날짜와 시간
    updated_at = models.DateTimeField(
        "마지막 수정일",
        auto_now=True,
    )

    def __str__(self):
        # 객체가 가진 필드값들을 하나의 문자열로 합쳐서 출력 확인할 때 이용
        # 지금은 아이디)이름) 만 출력 확인 처리함
        return f"{self.username} ({self.display_name})"


