"""회원가입, 로그인 세션, 회원정보, 관리자 회원관리 View를 정의합니다."""
# 사용자 인증/로그인/로그아웃 처리를 위한 함수를 가져옵니다.
from django.contrib.auth import login, logout
# 로그인한 사용자만 접근하도록 제한하는 데코레이터를 가져옵니다.
from django.contrib.auth.decorators import login_required, user_passes_test
# 처리 결과 메시지를 화면으로 전달하기 위한 messages 기능을 가져옵니다.
from django.contrib import messages
# HTTP 요청에 따라 페이지 렌더링, 이동, 객체 조회를 하기 위한 단축 함수를 가져옵니다.
from django.shortcuts import get_object_or_404, redirect, render
# 게시판 메인 화면에서 최근 게시글을 보여주기 위해 Board 모델을 가져옵니다.
from boards.models import Board
# 회원 관련 폼을 가져옵니다.
from .forms import LoginForm, ProfileUpdateForm, SignUpForm
# 회원 모델을 가져옵니다.
from .models import Member


def home(request):
    """로그인 여부와 관계없이 접근 가능한 첫 화면을 출력합니다."""
    # ORM을 이용해 최근 게시글 5개만 조회합니다.
    recent_posts = Board.objects.select_related("author").all()[:5]
    # 조회 결과를 home.html 템플릿에 전달합니다.
    return render(request, "home.html", {"recent_posts": recent_posts})


def signup_view(request):
    """GET이면 회원가입 화면, POST이면 새 회원을 저장합니다."""
    # 이미 로그인한 사용자는 중복 회원가입을 막고 메인으로 이동시킵니다.
    if request.user.is_authenticated:
        return redirect("home")
    # POST 요청이면 전송된 일반 값과 업로드 파일을 폼에 바인딩합니다.
    if request.method == "POST":
        form = SignUpForm(request.POST, request.FILES)
        # Django의 필드 검증과 비밀번호 일치/강도 검사를 모두 통과했는지 확인합니다.
        if form.is_valid():
            # UserCreationForm.save()가 비밀번호를 평문이 아닌 안전한 해시로 저장합니다.
            member = form.save()
            # 회원가입 직후 자동 로그인하여 세션을 생성합니다.
            login(request, member)
            # 다음 화면에서 보여줄 성공 메시지를 세션에 저장합니다.
            messages.success(request, "회원가입과 로그인이 완료되었습니다.")
            # 게시판 목록으로 이동합니다.
            return redirect("boards:list")
    else:
        # GET 요청이면 빈 회원가입 폼을 생성합니다.
        form = SignUpForm()
    # 오류가 있거나 GET 요청이면 폼 화면을 출력합니다.
    return render(request, "members/signup.html", {"form": form})


def login_view(request):
    """아이디/비밀번호를 검증하고 성공 시 Django 로그인 세션을 생성합니다."""
    # 이미 로그인한 사용자는 게시판으로 이동시킵니다.
    if request.user.is_authenticated:
        return redirect("boards:list")
    # AuthenticationForm에 현재 request와 POST 데이터를 전달합니다.
    form = LoginForm(request=request, data=request.POST or None)
    # POST 요청이며 아이디/비밀번호 검증에 성공한 경우 처리합니다.
    if request.method == "POST" and form.is_valid():
        # 검증 완료된 사용자 객체를 가져옵니다.
        member = form.get_user()
        # login()이 세션에 사용자 PK와 인증 백엔드 정보를 안전하게 저장합니다.
        login(request, member)
        # 로그인 성공 메시지를 저장합니다.
        messages.success(request, f"{member.display_name}님, 로그인되었습니다.")
        # 로그인 전에 접근하려던 URL(next)이 있으면 그곳으로, 없으면 게시판으로 이동합니다.
        return redirect(request.GET.get("next") or "boards:list")
    # 로그인 화면을 출력합니다.
    return render(request, "members/login.html", {"form": form})


@login_required
def logout_view(request):
    """현재 로그인 세션을 제거하여 로그아웃합니다."""
    # 상태 변경 작업은 POST 요청에서만 처리합니다.
    if request.method == "POST":
        # logout()이 현재 세션의 인증 데이터를 제거하고 세션을 안전하게 정리합니다.
        logout(request)
        # 로그아웃 안내 메시지를 저장합니다.
        messages.success(request, "로그아웃되었습니다.")
    # 메인 화면으로 이동합니다.
    return redirect("home")


@login_required
def profile_view(request):
    """로그인한 본인의 회원 정보를 조회합니다."""
    # request.user는 AuthenticationMiddleware가 세션을 기준으로 구성한 Member 객체입니다.
    return render(request, "members/profile.html", {"member": request.user})


@login_required
def profile_update_view(request):
    """로그인 사용자가 본인의 회원 정보를 수정합니다."""
    # POST이면 입력값/파일을 기존 회원 객체에 바인딩하고, GET이면 기존 값이 채워진 폼을 만듭니다.
    form = ProfileUpdateForm(request.POST or None, request.FILES or None, instance=request.user)
    # POST 요청이고 유효성 검사를 통과하면 DB에 UPDATE SQL에 해당하는 ORM 작업을 수행합니다.
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "회원 정보가 수정되었습니다.")
        return redirect("members:profile")
    # 수정 폼을 출력합니다.
    return render(request, "members/profile_form.html", {"form": form})


@login_required
def withdraw_view(request):
    """로그인한 사용자가 본인 계정을 탈퇴합니다."""
    # 실수로 GET 요청만으로 삭제되지 않도록 POST에서만 실제 삭제합니다.
    if request.method == "POST":
        # 현재 로그인한 회원 객체를 보관합니다.
        member = request.user
        # 먼저 로그아웃하여 세션에서 사용자 인증 정보를 제거합니다.
        logout(request)
        # 회원 삭제 시 Board.author의 CASCADE 설정에 따라 해당 사용자의 글도 함께 삭제됩니다.
        member.delete()
        messages.success(request, "회원 탈퇴가 완료되었습니다.")
        return redirect("home")
    # 확인 화면을 출력합니다.
    return render(request, "members/withdraw_confirm.html")


def _is_admin(user):
    """staff 또는 superuser인지 검사하여 관리자 전용 View에서 재사용합니다."""
    # 인증된 사용자이면서 Django 관리자 권한 플래그가 하나라도 있으면 True를 반환합니다.
    return user.is_authenticated and (user.is_staff or user.is_superuser)


@user_passes_test(_is_admin)
def member_list_view(request):
    """관리자가 일반 회원 목록을 조회합니다."""
    # superuser를 제외한 회원을 최근 가입순으로 조회합니다.
    members = Member.objects.filter(is_superuser=False).order_by("-date_joined")
    # 관리자 회원 목록 화면을 출력합니다.
    return render(request, "members/member_list.html", {"members": members})


@user_passes_test(_is_admin)
def toggle_active_view(request, pk):
    """관리자가 일반 회원의 로그인 허용/제한 상태를 변경합니다."""
    # URL의 PK로 대상 회원을 조회하고 없으면 404를 반환합니다.
    member = get_object_or_404(Member, pk=pk, is_superuser=False)
    # GET으로 상태 변경이 되지 않도록 POST에서만 처리합니다.
    if request.method == "POST":
        # 현재 활성 상태를 반대로 변경하여 원본 LOGIN_OK 토글 기능을 구현합니다.
        member.is_active = not member.is_active
        # 변경한 is_active 필드만 UPDATE하도록 저장합니다.
        member.save(update_fields=["is_active"])
        messages.success(request, f"{member.username}의 로그인 상태를 {'허용' if member.is_active else '제한'}으로 변경했습니다.")
    # 회원 목록으로 이동합니다.
    return redirect("members:member_list")
