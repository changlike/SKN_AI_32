"""Spring MVC의 Board DTO/BOARD 테이블을 Django ORM 모델로 변환한 파일입니다."""
# settings.AUTH_USER_MODEL을 참조하기 위해 settings를 가져옵니다.
from django.conf import settings
# ORM 필드 및 모델 기반 클래스를 사용하기 위해 models를 가져옵니다.
from django.db import models


class Board(models.Model):
    """로그인 회원이 작성하고 소유권 기반으로 수정/삭제하는 게시글 모델입니다."""
    # 원본 BOARD_WRITER를 회원 테이블에 대한 외래키로 변환합니다.
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="boards", verbose_name="작성자")
    # 원본 BOARD_TITLE에 대응합니다.
    title = models.CharField("제목", max_length=100)
    # 원본 BOARD_CONTENT에 대응합니다.
    content = models.TextField("내용")
    # 원본 첨부파일 관련 두 필드를 Django FileField 하나로 단순화하여 실제 저장 경로까지 관리합니다.
    attachment = models.FileField("첨부파일", upload_to="board_files/%Y/%m/%d/", blank=True, null=True)
    # 원본 BOARD_READCOUNT에 대응하는 조회수입니다.
    read_count = models.PositiveIntegerField("조회수", default=0)
    # 원본 BOARD_DATE에 대응하며 최초 작성 시각을 자동 저장합니다.
    created_at = models.DateTimeField("작성일", auto_now_add=True)
    # 게시글 수정 시각을 자동 저장합니다.
    updated_at = models.DateTimeField("수정일", auto_now=True)

    class Meta:
        # 최신 글이 먼저 나오도록 기본 정렬합니다.
        ordering = ["-id"]
        # 관리자 화면에서 표시할 단수 이름입니다.
        verbose_name = "게시글"
        # 관리자 화면에서 표시할 복수 이름입니다.
        verbose_name_plural = "게시글"

    def __str__(self):
        """게시글 객체를 제목으로 표시합니다."""
        # 관리자 화면 등에서 제목이 보이도록 반환합니다.
        return self.title

    def can_edit(self, user):
        """수정 권한은 작성자 본인에게만 허용합니다."""
        # 로그인한 사용자의 PK와 작성자 PK가 같은 경우에만 True입니다.
        return user.is_authenticated and self.author_id == user.id

    def can_delete(self, user):
        """삭제 권한은 작성자 본인 또는 관리자에게 허용합니다."""
        # 작성자 본인이거나 staff/superuser 관리자이면 삭제할 수 있습니다.
        return user.is_authenticated and (self.author_id == user.id or user.is_staff or user.is_superuser)
