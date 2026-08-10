# members/views.py

# Django 로그인/로그아웃 기능
from django.contrib.auth import login, logout

# 성공 안내 메시지
from django.contrib import messages

# HTML 출력과 URL 이동 기능
from django.shortcuts import render, redirect

# 회원 관련 Form
from .forms import SignUpForm, LoginForm

def signup_view(request):
    """ 회원가입 처리 View 입니다. """

    # POST 요청이면, 사용자가 입력한 데이터를 받음
    if request.method == 'POST':
        # 일반 데이터와 업로드 파일을 Form에 전달함
        form = SignUpForm(request.POST, request.FILES)

        # 입력값 검증 수행
        if form.is_valid():
            # 입력값들이 모두 유효하면,
            # 가입한 회원 정보를 db에 저장 처리함
            # 비밀번호는 평문이 아닌 해시로 저장됨
            member = form.save()

            # 가입한 사용자를 즉시 로그인 처리함
            # 이때 Django Session이 생성됨
            login(request, member)

            messages.success(
                request,
                "회원 가입이 완료되었습니다."
            )

            # 첫 페이지로 이동
            return redirect('/home')
    else:
        # GET 요청이면 빈 회원가입 Form을 만듦
        form = SignUpForm()
    # else end ------------------------------------------------

    return render(
        request,
        "members/signup.html",
        {"form": form}
    )
# 회원 가입 뷰 --------------------------------------------------------

# 로그인 뷰도 작성
def login_view(request):
    """회원 로그인 뷰입니다."""

    # Django AuthenticationForm 생성
    form = LoginForm(
        request=request,
        data=request.POST or None,)

    # POST 요청이면서 인증에 성공했다면
    if request.method == 'POST' and form.is_valid():
        # 인증된 회원 객체를 가져옴
        member = form.get_user()

        # Django 세션에 사용자 인증 정보를 저장함
        login(request, member)

        messages.success(
            request,
            f"{member.display_name}님 로그인되었습니다."
        )

        return redirect('/home')
    # if closed ---------------------------------------

    return render(
        request,
        "members/login.html",
        {"form": form}
    )
# def ---------------------------------------------------------

# 로그아웃 View 작성
from django.contrib.auth.decorators import login_required

@login_required
def logout_view(request):
    """현재 로그인한 사용자를 로그아웃 합니다."""
    if request.method == 'POST':
        # 현재 세션의 로그인 인증 정보를 제거함
        logout(request)

        messages.success(
            request,
            "로그아웃되었습니다."
        )
    # if close --------------------------------------------------------------------------

    return redirect('/home')














