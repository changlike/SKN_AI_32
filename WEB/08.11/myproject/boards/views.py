from django.shortcuts import render
from .models import Board

def board_list(request):
    """게시글 목록 페이지입니다."""
    # ORM을 사용해서 전체 게시글을 조회함: all() 사용
    # 작성자 정보도 함께 조회할 것임: 역참조임
    boards = Board.objects.select_related("author").all()
    return render(request, "boards/board_list.html", {"boards": boards})
# def board_list ----------------------------------------------

# 새 게시글 등록 View 추가 작성
# 등록용 form이 필요함 => 추가 임포트함
# 로그인한 회원만 새 게시글 등록할 수 있음
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from .forms import BoardForm

@login_required
def board_create(request):
    """로그인 사용자만 게시글을 새로 작성할 수 있습니다."""
    form = BoardForm(request.POST or None, request.FILES or None)

    if request.method == "POST" and form.is_valid():
        form.save()

