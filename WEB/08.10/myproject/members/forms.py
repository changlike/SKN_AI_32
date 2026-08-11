# members/forms.py

# Django Form 기능을 가져옴
from django import forms

# Django 기본 인증 폼을 가져옴
from django.contrib.auth.forms import (
    AuthenticationForm,
    UserCreationForm,
)

# 사용자 정의 Member 모델 가져옴
# 회원 모델을 가져옵니다.
from .models import Member

class SignUpForm(UserCreationForm):
    """회원가입 Form입니다."""

    class Meta:

        # 이 Form이 사용할 모델입니다.
        model = Member

        # 화면에서 입력할 필드입니다.
        fields = (
            "username",
            "display_name",
            "email",
            "gender",
            "age",
            "phone",
            "photo",
            "password1",
            "password2",
        )

    def __init__(self, *args, **kwargs):

        # 부모 클래스 초기화를 실행합니다.
        super().__init__(*args, **kwargs)

        # 모든 입력 요소에 CSS 클래스를 추가합니다.
        for field in self.fields.values():

            field.widget.attrs.setdefault(
                "class",
                "form-control"
            )
# class SignUpForm --------------------------------------------------------

# 로그인 Form 만들기
class LoginForm(AuthenticationForm):
    """로그인 Form입니다."""

    def __init__(
        self,
        request=None,
        *args,
        **kwargs
    ):

        # Django 기본 AuthenticationForm을 초기화합니다.
        super().__init__(
            request=request,
            *args,
            **kwargs
        )

        # 아이디 입력창 CSS를 지정합니다.
        self.fields["username"].widget.attrs.update({
            "class": "form-control",
            "placeholder": "회원 아이디"
        })

        # 비밀번호 입력창 CSS를 지정합니다.
        self.fields["password"].widget.attrs.update({
            "class": "form-control",
            "placeholder": "비밀번호"
        })









