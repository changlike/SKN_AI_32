# members/forms.py

# Django Form 기능을 가져옴
from django import forms


# Django 기본 인증 폼을 가져옴
from django.contrib.auth.forms import(
    AuthenticationForm,
    UserCreationForm,
)

# 사용자 정의 Member 모델 가져옴
from .models import Member

class SignUpForm(UserCreationForm):
    """ 회원 가입 Form 입니다."""

    class Meta:

        # 이 Form이 사용할 모댈 선언함
        model = Member

        # 화면에서 입력할 필드
        fields = (
            'username',
            'display_name',
            'email',
            'gender',
            'phone',
            'password1',
            'password2',
        )
    # class Meta ------------------------------------------------

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 모든 입력 요소에 CSS 클래스를 추가함
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')

    # class SignUpForm -------------------------------------------

# 로그인 Form 만들기
class LoginForm(AuthenticationForm):
    """로그인 Form 입니다."""
    def __init__(self, request=None, *args, **kwargs):

        # Django 기본 AuthenticationForm을 초기화함
        super().__init__(request,*args, **kwargs)

        # 아이디 입력 필드 CSS 지정
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': "회원 아이디 입력"})

        # 비밀번호 입력 필드 CSS 지정
        self.fields['password'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': "비밀번호 입력"})