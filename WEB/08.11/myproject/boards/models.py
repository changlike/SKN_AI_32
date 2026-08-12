# 게시글 작성 시 로그인한 사용자 아이디(예:user01)를 글작성자(author)에 자동 기록되게 하기 위해
# settings의 AUTH_USER_MODEL를 사용함
from django.conf import settings

from django.db import models

class Board(models.Model):
    "게시글 모델입니다."

    # 게시글 작성자
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        # 회원이 삭제되면, 해당 회원의 게시글도 삭제함
        on_delete=models.CASCADE,
        # 역참조 이름 지정
        related_name="boards",)

    # 게시글 제목
    title = models.CharField("제목", max_length=200)

    # 게시글 본문
    content = models.TextField("내용")

    # 첨부파일
    attachment = models.FileField(
        "첨부파일",
        upload_to="board_files/%Y/%m/",
        null=True,
        blank=True,
    )

    # 조회수
    read_count = models.PositiveIntegerField("조회수", default=0)

    # 작성 시각
    created_at = models.DateTimeField("작성일", auto_now_add=True)
    # 수정 시각
    updated_at = models.DateTimeField("수정일", auto_now=True)

    class Meta:
        # 가장 최근 글부터 보여줌
        ordering = ["-created_at"]
    # class Meta -------------------------------

    def __str__(self):
        return self.title + "," + self.author

    # 수정 권한에 대한 메소드 추가
    def can_edit(self, user):
        """게시글 수정 가능 여부를 반환합니다."""
        # 로그인 상태이고, 게시글 작성자와 현재 로그인한 사용자가 같아야 함
        return (user.is_authenticated and self.author.id == user.id)

    # 삭제 권한에 대한 메소드 추가
    def can_delete(self, user):
        """게시글 삭제 가능 여부를 검사합니다."""
        # 비로그인 상태이면 삭제할 수 없음
        if not user.is_authenticated:
            return False

        # 로그인 상태이고, 본인 게시글이면 삭제할 수 있음
        if self.author.id == user.id:
            return True

        # 관리자이면 모든 게시글 삭제 가능
        if user.is_staff or user.is_superuser:
            return True

        return False

    # class Board -----------------------------------
