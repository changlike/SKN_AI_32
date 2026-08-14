"""React 프론트엔드용 게시판 JSON API입니다. 기존 Board 모델/Form/권한 정책을 그대로 재사용합니다."""
from django.core.paginator import Paginator
from django.db.models import F, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views import View

from api.helpers import JsonLoginRequiredMixin, board_to_dict, form_errors, json_error
from .forms import BoardForm
from .models import Board


class BoardListAPIView(View):
    def get(self, request):
        query = request.GET.get("q", "").strip()
        boards = Board.objects.select_related("author").all()
        if query:
            boards = boards.filter(Q(title__icontains=query) | Q(content__icontains=query))
        paginator = Paginator(boards, 10)
        page_obj = paginator.get_page(request.GET.get("page"))
        return JsonResponse({
            "ok": True,
            "query": query,
            "items": [board_to_dict(board, request) for board in page_obj.object_list],
            "pagination": {
                "page": page_obj.number,
                "num_pages": paginator.num_pages,
                "count": paginator.count,
                "has_previous": page_obj.has_previous(),
                "has_next": page_obj.has_next(),
                "previous_page": page_obj.previous_page_number() if page_obj.has_previous() else None,
                "next_page": page_obj.next_page_number() if page_obj.has_next() else None,
            },
        }, json_dumps_params={"ensure_ascii": False})


class BoardDetailAPIView(View):
    def get(self, request, pk):
        board = get_object_or_404(Board.objects.select_related("author"), pk=pk)
        Board.objects.filter(pk=board.pk).update(read_count=F("read_count") + 1)
        board.read_count += 1
        return JsonResponse({"ok": True, "board": board_to_dict(board, request, include_content=True)}, json_dumps_params={"ensure_ascii": False})


class BoardCreateAPIView(JsonLoginRequiredMixin, View):
    def post(self, request):
        form = BoardForm(request.POST, request.FILES)
        if not form.is_valid():
            return json_error("게시글 입력값을 확인하세요.", 400, form_errors(form))
        board = form.save(commit=False)
        board.author = request.user
        board.save()
        board = Board.objects.select_related("author").get(pk=board.pk)
        return JsonResponse({"ok": True, "message": "게시글이 등록되었습니다.", "board": board_to_dict(board, request, include_content=True)}, status=201, json_dumps_params={"ensure_ascii": False})


class BoardUpdateAPIView(JsonLoginRequiredMixin, View):
    def _get_board(self, request, pk):
        board = get_object_or_404(Board, pk=pk)
        if not board.can_edit(request.user):
            return None
        return board

    def get(self, request, pk):
        # 기존 수정 화면과 동일하게 조회수를 증가시키지 않고 현재 게시글 값을 반환합니다.
        board = self._get_board(request, pk)
        if board is None:
            return json_error("본인이 작성한 게시글만 수정할 수 있습니다.", 403)
        board = Board.objects.select_related("author").get(pk=board.pk)
        return JsonResponse({"ok": True, "board": board_to_dict(board, request, include_content=True)}, json_dumps_params={"ensure_ascii": False})

    def post(self, request, pk):
        board = self._get_board(request, pk)
        if board is None:
            return json_error("본인이 작성한 게시글만 수정할 수 있습니다.", 403)
        form = BoardForm(request.POST, request.FILES, instance=board)
        if not form.is_valid():
            return json_error("게시글 입력값을 확인하세요.", 400, form_errors(form))
        board = form.save()
        board = Board.objects.select_related("author").get(pk=board.pk)
        return JsonResponse({"ok": True, "message": "게시글이 수정되었습니다.", "board": board_to_dict(board, request, include_content=True)}, json_dumps_params={"ensure_ascii": False})


class BoardDeleteAPIView(JsonLoginRequiredMixin, View):
    def post(self, request, pk):
        board = get_object_or_404(Board.objects.select_related("author"), pk=pk)
        if not board.can_delete(request.user):
            return json_error("본인 글만 삭제할 수 있습니다.", 403)
        if board.attachment:
            board.attachment.delete(save=False)
        board.delete()
        return JsonResponse({"ok": True, "message": "게시글이 삭제되었습니다."}, json_dumps_params={"ensure_ascii": False})
