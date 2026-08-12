"""게시글 목록/상세/등록/수정/삭제 CRUD와 소유권 검사를 담당합니다."""
# 로그인 제한 View에 사용할 데코레이터를 가져옵니다.
from django.contrib.auth.decorators import login_required
# 성공/오류 메시지를 화면에 전달하기 위한 messages를 가져옵니다.
from django.contrib import messages
# 페이지 단위로 게시글을 나누기 위한 Paginator를 가져옵니다.
from django.core.paginator import Paginator
# 권한이 없을 때 HTTP 403을 발생시킬 예외를 가져옵니다.
from django.core.exceptions import PermissionDenied
# 조회수를 안전하게 DB에서 1 증가시키기 위한 F 표현식을 가져옵니다.
from django.db.models import F, Q
# 렌더링, 객체 조회, 리다이렉트 단축 함수를 가져옵니다.
from django.shortcuts import get_object_or_404, redirect, render
# 게시글 입력 폼을 가져옵니다.
from .forms import BoardForm
# 게시글 모델을 가져옵니다.
from .models import Board


def board_list(request):
    """게시글 전체 목록을 검색과 페이징을 적용하여 출력합니다."""
    # URL의 q 검색어를 가져오고 앞뒤 공백을 제거합니다.
    query = request.GET.get("q", "").strip()
    # N+1 문제를 줄이기 위해 author를 JOIN 형태로 함께 가져옵니다.
    boards = Board.objects.select_related("author").all()
    # 검색어가 있으면 제목 또는 내용에 검색어가 포함된 게시글만 조회합니다.
    if query:
        boards = boards.filter(Q(title__icontains=query) | Q(content__icontains=query))
    # 한 페이지에 10개 게시글을 출력하도록 Paginator를 생성합니다.
    paginator = Paginator(boards, 10)
    # page 파라미터 값을 받아 유효하지 않아도 안전하게 페이지 객체를 반환합니다.
    page_obj = paginator.get_page(request.GET.get("page"))
    # 목록, 검색어, 페이지 정보를 템플릿으로 전달합니다.
    return render(request, "boards/board_list.html", {"page_obj": page_obj, "query": query})


def board_detail(request, pk):
    """게시글 상세 내용을 출력하고 조회수를 1 증가시킵니다."""
    # 작성자 정보와 함께 PK에 해당하는 게시글을 조회합니다.
    board = get_object_or_404(Board.objects.select_related("author"), pk=pk)
    # F 표현식을 사용하면 동시 요청에서도 현재 DB 값 기준으로 +1 UPDATE가 수행됩니다.
    Board.objects.filter(pk=board.pk).update(read_count=F("read_count") + 1)
    # 화면에 최신 조회수를 표시하기 위해 현재 객체 값을 1 증가시킵니다.
    board.read_count += 1
    # 상세 페이지를 출력합니다.
    return render(request, "boards/board_detail.html", {"board": board})


@login_required
def board_create(request):
    """로그인한 회원만 새 게시글을 등록할 수 있습니다."""
    # POST이면 전송 데이터와 파일을 폼에 바인딩하고 GET이면 빈 폼을 만듭니다.
    form = BoardForm(request.POST or None, request.FILES or None)
    # POST이면서 폼 검증에 성공한 경우 DB에 INSERT합니다.
    if request.method == "POST" and form.is_valid():
        # 작성자 값을 request.user로 넣기 위해 commit=False로 아직 DB 저장하지 않습니다.
        board = form.save(commit=False)
        # 작성자 조작을 막기 위해 브라우저 입력값이 아니라 로그인 세션의 사용자를 지정합니다.
        board.author = request.user
        # 최종 게시글을 ORM save()로 DB에 INSERT합니다.
        board.save()
        messages.success(request, "게시글이 등록되었습니다.")
        # 작성한 글 상세 화면으로 이동합니다.
        return redirect("boards:detail", pk=board.pk)
    # 등록 폼을 출력합니다.
    return render(request, "boards/board_form.html", {"form": form, "mode": "등록"})


@login_required
def board_update(request, pk):
    """작성자 본인만 게시글을 수정할 수 있습니다."""
    # URL PK로 수정 대상 게시글을 조회합니다.
    board = get_object_or_404(Board, pk=pk)
    # 모델의 can_edit()로 본인 글인지 검사합니다.
    if not board.can_edit(request.user):
        # 관리자를 포함해 작성자가 아니면 수정은 허용하지 않고 403을 반환합니다.
        raise PermissionDenied("본인이 작성한 게시글만 수정할 수 있습니다.")
    # 기존 게시글 인스턴스에 입력값을 바인딩하여 UPDATE 폼을 만듭니다.
    form = BoardForm(request.POST or None, request.FILES or None, instance=board)
    # POST 요청이며 유효성 검사에 성공하면 UPDATE합니다.
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "게시글이 수정되었습니다.")
        return redirect("boards:detail", pk=board.pk)
    # 수정 폼을 출력합니다.
    return render(request, "boards/board_form.html", {"form": form, "mode": "수정", "board": board})


@login_required
def board_delete(request, pk):
    """작성자 본인 또는 관리자만 게시글을 삭제할 수 있습니다."""
    # 삭제 대상 게시글을 작성자 정보와 함께 조회합니다.
    board = get_object_or_404(Board.objects.select_related("author"), pk=pk)
    # 작성자 또는 관리자 여부를 검사합니다.
    if not board.can_delete(request.user):
        # 권한이 없으면 403 Forbidden을 발생시킵니다.
        raise PermissionDenied("본인 글만 삭제할 수 있습니다.")
    # GET 요청에서는 바로 지우지 않고 삭제 확인 화면을 보여줍니다.
    if request.method == "POST":
        # 첨부파일이 존재하면 스토리지에서도 파일을 삭제합니다.
        if board.attachment:
            board.attachment.delete(save=False)
        # ORM delete()를 호출하여 게시글 레코드를 삭제합니다.
        board.delete()
        messages.success(request, "게시글이 삭제되었습니다.")
        return redirect("boards:list")
    # 삭제 확인 화면을 출력합니다.
    return render(request, "boards/board_confirm_delete.html", {"board": board})
