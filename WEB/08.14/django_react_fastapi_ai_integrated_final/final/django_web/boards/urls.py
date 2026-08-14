"""게시판 앱의 URL과 클래스 기반 View를 연결합니다."""
# URL 패턴을 작성하기 위해 path를 가져옵니다.
from django.urls import path
# 같은 앱의 views 모듈을 가져옵니다.
from . import views

# 템플릿에서 boards:list와 같은 이름공간을 사용하기 위한 앱 이름입니다.
app_name = "boards"

# 기존 URL 경로와 name은 그대로 유지하고 View 연결만 as_view() 방식으로 변경합니다.
urlpatterns = [
    path("", views.BoardListView.as_view(), name="list"),
    path("create/", views.BoardCreateView.as_view(), name="create"),
    path("<int:pk>/", views.BoardDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", views.BoardUpdateView.as_view(), name="update"),
    path("<int:pk>/delete/", views.BoardDeleteView.as_view(), name="delete"),
]
