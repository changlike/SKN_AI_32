"""React SPA용 Django JSON API에서 공통으로 사용하는 직렬화/응답 도우미입니다."""
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin


class JsonLoginRequiredMixin(LoginRequiredMixin):
    """API 인증 실패를 HTML 리다이렉트가 아니라 JSON 401로 반환합니다."""
    def handle_no_permission(self):
        return json_error("로그인이 필요합니다.", 401)



def json_error(message, status=400, errors=None):
    payload = {"ok": False, "message": str(message)}
    if errors is not None:
        payload["errors"] = errors
    return JsonResponse(payload, status=status, json_dumps_params={"ensure_ascii": False})


def form_errors(form):
    return {name: [str(message) for message in messages] for name, messages in form.errors.items()}


def member_to_dict(member, request=None):
    photo_url = None
    if getattr(member, "photo", None):
        try:
            photo_url = member.photo.url
            if request is not None:
                photo_url = request.build_absolute_uri(photo_url)
        except ValueError:
            photo_url = None
    return {
        "id": member.pk,
        "username": member.username,
        "display_name": member.display_name,
        "email": member.email,
        "gender": member.gender,
        "gender_label": member.get_gender_display(),
        "age": member.age,
        "phone": member.phone,
        "photo_url": photo_url,
        "sign_type": member.sign_type,
        "is_active": member.is_active,
        "is_staff": member.is_staff,
        "is_superuser": member.is_superuser,
        "admin_yn": member.admin_yn,
        "login_ok": member.login_ok,
        "date_joined": member.date_joined.isoformat() if member.date_joined else None,
        "updated_at": member.updated_at.isoformat() if member.updated_at else None,
    }


def board_to_dict(board, request=None, include_content=False):
    attachment_url = None
    if getattr(board, "attachment", None):
        try:
            attachment_url = board.attachment.url
            if request is not None:
                attachment_url = request.build_absolute_uri(attachment_url)
        except ValueError:
            attachment_url = None
    data = {
        "id": board.pk,
        "title": board.title,
        "author": {
            "id": board.author_id,
            "username": board.author.username,
            "display_name": board.author.display_name,
        },
        "attachment_url": attachment_url,
        "attachment_name": board.attachment.name.split("/")[-1] if board.attachment else None,
        "read_count": board.read_count,
        "created_at": board.created_at.isoformat() if board.created_at else None,
        "updated_at": board.updated_at.isoformat() if board.updated_at else None,
    }
    if include_content:
        data["content"] = board.content
    return data
