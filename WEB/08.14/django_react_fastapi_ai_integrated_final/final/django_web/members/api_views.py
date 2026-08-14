"""React 프론트엔드가 사용하는 회원/세션 JSON API입니다.
기존 members.views의 서비스 동작은 변경하지 않고 같은 Model/Form/Auth 기능을 API 형식으로 제공합니다.
"""
from django.contrib.auth import login, logout
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404
from django.views import View

from api.helpers import JsonLoginRequiredMixin, form_errors, json_error, member_to_dict
from .forms import LoginForm, ProfileUpdateForm, SignUpForm
from .models import Member


class CsrfView(View):
    def get(self, request):
        return JsonResponse({"ok": True, "csrfToken": get_token(request)}, json_dumps_params={"ensure_ascii": False})


class SessionView(View):
    def get(self, request):
        return JsonResponse({
            "ok": True,
            "authenticated": request.user.is_authenticated,
            "user": member_to_dict(request.user, request) if request.user.is_authenticated else None,
        }, json_dumps_params={"ensure_ascii": False})


class SignUpAPIView(View):
    def post(self, request):
        if request.user.is_authenticated:
            return json_error("이미 로그인되어 있습니다.", status=409)
        form = SignUpForm(request.POST, request.FILES)
        if not form.is_valid():
            return json_error("회원가입 입력값을 확인하세요.", 400, form_errors(form))
        member = form.save()
        login(request, member)
        return JsonResponse({"ok": True, "message": "회원가입과 로그인이 완료되었습니다.", "user": member_to_dict(member, request)}, status=201, json_dumps_params={"ensure_ascii": False})


class LoginAPIView(View):
    def post(self, request):
        if request.user.is_authenticated:
            return JsonResponse({"ok": True, "message": "이미 로그인되어 있습니다.", "user": member_to_dict(request.user, request)}, json_dumps_params={"ensure_ascii": False})
        form = LoginForm(request=request, data=request.POST)
        if not form.is_valid():
            return json_error("아이디 또는 비밀번호를 확인하세요.", 400, form_errors(form))
        member = form.get_user()
        login(request, member)
        return JsonResponse({"ok": True, "message": f"{member.display_name}님, 로그인되었습니다.", "user": member_to_dict(member, request)}, json_dumps_params={"ensure_ascii": False})


class LogoutAPIView(JsonLoginRequiredMixin, View):
    def post(self, request):
        logout(request)
        return JsonResponse({"ok": True, "message": "로그아웃되었습니다."}, json_dumps_params={"ensure_ascii": False})


class ProfileAPIView(JsonLoginRequiredMixin, View):
    def get(self, request):
        return JsonResponse({"ok": True, "user": member_to_dict(request.user, request)}, json_dumps_params={"ensure_ascii": False})

    def post(self, request):
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if not form.is_valid():
            return json_error("회원 정보 입력값을 확인하세요.", 400, form_errors(form))
        member = form.save()
        return JsonResponse({"ok": True, "message": "회원 정보가 수정되었습니다.", "user": member_to_dict(member, request)}, json_dumps_params={"ensure_ascii": False})


class WithdrawAPIView(JsonLoginRequiredMixin, View):
    def post(self, request):
        member = request.user
        logout(request)
        member.delete()
        return JsonResponse({"ok": True, "message": "회원 탈퇴가 완료되었습니다."}, json_dumps_params={"ensure_ascii": False})


def _is_admin(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)


class MemberListAPIView(JsonLoginRequiredMixin, View):
    def get(self, request):
        if not _is_admin(request.user):
            return json_error("관리자만 접근할 수 있습니다.", 403)
        members = Member.objects.filter(is_superuser=False).order_by("-date_joined")
        return JsonResponse({"ok": True, "members": [member_to_dict(member, request) for member in members]}, json_dumps_params={"ensure_ascii": False})


class ToggleActiveAPIView(JsonLoginRequiredMixin, View):
    def post(self, request, pk):
        if not _is_admin(request.user):
            return json_error("관리자만 접근할 수 있습니다.", 403)
        member = get_object_or_404(Member, pk=pk, is_superuser=False)
        member.is_active = not member.is_active
        member.save(update_fields=["is_active"])
        return JsonResponse({
            "ok": True,
            "message": f"{member.username}의 로그인 상태를 {'허용' if member.is_active else '제한'}으로 변경했습니다.",
            "member": member_to_dict(member, request),
        }, json_dumps_params={"ensure_ascii": False})
