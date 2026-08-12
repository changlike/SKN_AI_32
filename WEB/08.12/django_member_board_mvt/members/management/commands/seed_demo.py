"""수업 실습용 관리자/일반회원/게시글 데이터를 생성하는 관리 명령입니다."""
# Django 관리 명령 기반 클래스를 가져옵니다.
from django.core.management.base import BaseCommand
# 회원 모델을 가져옵니다.
from members.models import Member
# 게시글 모델을 가져옵니다.
from boards.models import Board


class Command(BaseCommand):
    """python manage.py seed_demo 명령을 구현합니다."""
    # help 옵션에 표시될 설명입니다.
    help = "admin, user01, user02와 예제 게시글을 생성합니다."

    def handle(self, *args, **options):
        """중복 실행해도 기존 계정을 재사용하도록 데모 데이터를 생성합니다."""
        # 관리자 계정을 조회하거나 처음 실행이면 생성합니다.
        admin, created = Member.objects.get_or_create(username="admin", defaults={"display_name": "관리자", "email": "admin@example.com", "is_staff": True, "is_superuser": True})
        # 관리자 계정이 새로 생성된 경우 실습용 비밀번호를 해시하여 저장합니다.
        if created:
            admin.set_password("admin1234!")
            admin.save()
        # 일반 사용자 user01을 조회하거나 생성합니다.
        user01, created = Member.objects.get_or_create(username="user01", defaults={"display_name": "홍길동", "email": "user01@example.com", "gender": "M", "age": 25})
        # 새 user01 계정에만 초기 비밀번호를 설정합니다.
        if created:
            user01.set_password("pass1234!")
            user01.save()
        # 일반 사용자 user02를 조회하거나 생성합니다.
        user02, created = Member.objects.get_or_create(username="user02", defaults={"display_name": "신사임당", "email": "user02@example.com", "gender": "F", "age": 45})
        # 새 user02 계정에만 초기 비밀번호를 설정합니다.
        if created:
            user02.set_password("pass1234!")
            user02.save()
        # 게시글이 하나도 없을 때만 예제 글을 생성하여 중복 데이터를 방지합니다.
        if not Board.objects.exists():
            Board.objects.create(author=admin, title="관리자 게시글", content="Django MVT 변환 프로젝트에 오신 것을 환영합니다.")
            Board.objects.create(author=user01, title="Django ORM 실습", content="Model 클래스를 통해 SQL 없이 게시글을 조회하고 저장합니다.")
            Board.objects.create(author=user02, title="세션과 권한", content="로그인 사용자와 작성자를 비교해 수정 및 삭제 권한을 제어합니다.")
        # 콘솔에 실습 계정 정보를 출력합니다.
        self.stdout.write(self.style.SUCCESS("데모 데이터 생성 완료: admin/admin1234!, user01/pass1234!, user02/pass1234!"))
