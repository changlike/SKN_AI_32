"""React 홈 화면에 필요한 기존 최근 게시글 서비스를 JSON으로 제공합니다."""
from django.http import JsonResponse
from django.views import View
from api.helpers import board_to_dict
from boards.models import Board


class HomeAPIView(View):
    def get(self, request):
        recent_posts = Board.objects.select_related("author").all()[:5]
        return JsonResponse({"ok": True, "recent_posts": [board_to_dict(board, request) for board in recent_posts]}, json_dumps_params={"ensure_ascii": False})
