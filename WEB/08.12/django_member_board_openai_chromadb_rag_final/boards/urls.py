"""게시판 앱의 URL과 CRUD View를 연결합니다."""
# URL 패턴 선언 함수를 가져옵니다.
from django.urls import path
# 같은 앱의 views를 가져옵니다.
from . import views

# 템플릿 reverse URL에서 boards:detail 형태로 사용할 이름공간입니다.
app_name = "boards"

# 게시판 CRUD URL을 정의합니다.
urlpatterns = [
    path("", views.board_list, name="list"),
    path("create/", views.board_create, name="create"),
    path("<int:pk>/", views.board_detail, name="detail"),
    path("<int:pk>/edit/", views.board_update, name="update"),
    path("<int:pk>/delete/", views.board_delete, name="delete"),
]
