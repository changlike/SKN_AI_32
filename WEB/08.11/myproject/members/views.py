# members/views.py

# Django 로그인/로그아웃 기능입니다.
from django.contrib.auth import login, logout

# 성공 안내 메시지 기능입니다.
from django.contrib import messages

# HTML 출력과 URL 이동 기능입니다.
from django.shortcuts import render, redirect

# 회원 관련 Form입니다.
from .forms import SignUpForm, LoginForm
# 회원 모델을 가져옵니다.
from .models import Member


def home(request):
    """로그인 여부와 관계없이 접근 가능한 첫 화면을 출력합니다."""
    # 로그인 성공 시 Django가 자동으로 request.user 정보를 Template에 전달하게 됨
    return render(request, "home.html")


def signup_view(request):
    """회원가입 처리 View입니다."""

    # POST 요청이면 사용자가 입력한 데이터를 받습니다.
    if request.method == "POST":

        # 일반 데이터와 업로드 파일을 Form에 전달합니다.
        form = SignUpForm(
            request.POST,
            request.FILES
        )

        # 입력값 검증을 수행합니다.
        if form.is_valid():

            # 회원을 DB에 저장합니다.
            # 비밀번호는 평문이 아닌 해시로 저장됩니다.
            member = form.save()

            # 가입한 사용자를 즉시 로그인 처리합니다.
            # 이때 Django Session이 생성됩니다.
            login(request, member)

            messages.success(
                request,
                "회원가입이 완료되었습니다."
            )

            return redirect("home")

    else:

        # GET 요청이면 빈 회원가입 Form을 만듭니다.
        form = SignUpForm()

    return render(
        request,
        "members/signup.html",
        {
            "form": form
        }
    )
# 회원 가입 뷰 ----------------------------------------

# 로그인 뷰도 작성
def login_view(request):
    """회원 로그인 View입니다."""

    # Django AuthenticationForm을 생성합니다.
    form = LoginForm(
        request=request,
        data=request.POST or None
    )

    # POST 요청이면서 인증에 성공했다면
    if request.method == "POST" and form.is_valid():

        # 인증된 회원 객체를 가져옵니다.
        member = form.get_user()

        # Django 세션에 사용자 인증정보를 저장합니다.
        login(request, member)

        messages.success(
            request,
            f"{member.display_name}님 로그인되었습니다."
        )

        return redirect("home")

    return render(
        request,
        "members/login.html",
        {
            "form": form
        }
    )
# def ------------------------------------------------

# 로그아웃 View 작성
from django.contrib.auth.decorators import login_required


@login_required
def logout_view(request):
    """현재 로그인 사용자를 로그아웃합니다."""
    logout(request)
    messages.success(
        request,
        "로그아웃되었습니다."
    )

    return redirect("home")

















