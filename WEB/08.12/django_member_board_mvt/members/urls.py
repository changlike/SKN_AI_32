"""회원 앱의 URL과 View를 연결합니다."""
# URL 패턴을 작성하기 위해 path를 가져옵니다.
from django.urls import path
# 같은 앱의 views 모듈을 가져옵니다.
from . import views

# 템플릿에서 members:login처럼 이름공간을 사용할 수 있도록 app_name을 지정합니다.
app_name = "members"

# 회원 관련 URL 패턴을 정의합니다.
urlpatterns = [
    path("signup/", views.signup_view, name="signup"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("profile/", views.profile_view, name="profile"),
    path("profile/edit/", views.profile_update_view, name="profile_edit"),
    path("withdraw/", views.withdraw_view, name="withdraw"),
    path("admin-list/", views.member_list_view, name="member_list"),
    path("<int:pk>/toggle-active/", views.toggle_active_view, name="toggle_active"),
]
