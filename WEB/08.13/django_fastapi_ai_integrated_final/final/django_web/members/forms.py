"""회원가입, 로그인, 회원정보 수정에 사용할 Django Form을 정의합니다."""
# Django의 사용자 생성/수정 폼 기반 클래스를 가져옵니다.
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
# 일반 ModelForm을 만들기 위한 forms 모듈을 가져옵니다.
from django import forms
# 현재 앱의 사용자 정의 회원 모델을 가져옵니다.
from .models import Member


class SignUpForm(UserCreationForm):
    """비밀번호 해시 저장까지 자동 처리하는 회원가입 폼입니다."""
    class Meta:
        # 저장 대상 모델을 사용자 정의 Member로 지정합니다.
        model = Member
        # 회원가입 화면에서 입력받을 필드를 순서대로 지정합니다.
        fields = ("username", "display_name", "email", "gender", "age", "phone", "photo", "password1", "password2")

    def __init__(self, *args, **kwargs):
        """Bootstrap 스타일과 한글 placeholder를 각 입력 위젯에 적용합니다."""
        # 부모 UserCreationForm의 초기화 로직을 먼저 실행합니다.
        super().__init__(*args, **kwargs)
        # 모든 폼 필드를 순회하면서 공통 CSS 클래스를 적용합니다.
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")


class LoginForm(AuthenticationForm):
    """Django authenticate()를 사용하는 세션 로그인 폼입니다."""
    def __init__(self, request=None, *args, **kwargs):
        """로그인 입력창에 공통 CSS 클래스를 적용합니다."""
        # 부모 AuthenticationForm 초기화를 수행합니다.
        super().__init__(request=request, *args, **kwargs)
        # 아이디 입력 필드 스타일을 지정합니다.
        self.fields["username"].widget.attrs.update({"class": "form-control", "placeholder": "회원 아이디"})
        # 비밀번호 입력 필드 스타일을 지정합니다.
        self.fields["password"].widget.attrs.update({"class": "form-control", "placeholder": "비밀번호"})


class ProfileUpdateForm(forms.ModelForm):
    """로그인 사용자가 본인의 회원 정보를 수정할 때 사용하는 폼입니다."""
    class Meta:
        # 수정 대상 모델을 Member로 지정합니다.
        model = Member
        # 아이디와 권한은 임의 수정하지 못하게 제외하고 일반 프로필 정보만 허용합니다.
        fields = ("display_name", "email", "gender", "age", "phone", "photo")

    def __init__(self, *args, **kwargs):
        """프로필 수정 입력 요소에 공통 CSS 클래스를 적용합니다."""
        # ModelForm 기본 초기화를 수행합니다.
        super().__init__(*args, **kwargs)
        # 모든 입력 위젯에 form-control 클래스를 부여합니다.
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")
