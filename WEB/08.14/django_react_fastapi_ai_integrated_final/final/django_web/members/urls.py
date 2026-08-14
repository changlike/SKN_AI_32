"""회원 앱의 URL과 클래스 기반 View를 연결합니다."""
# URL 패턴을 작성하기 위해 path를 가져옵니다.
from django.urls import path
# 같은 앱의 views 모듈을 가져옵니다.
from . import views

# 템플릿에서 members:login처럼 이름공간을 사용할 수 있도록 app_name을 지정합니다.
app_name = "members"

# 기존 URL 경로와 name은 그대로 유지하고 View 연결만 as_view() 방식으로 변경합니다.
urlpatterns = [
    path("signup/", views.SignUpView.as_view(), name="signup"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("profile/", views.ProfileView.as_view(), name="profile"),
    path("profile/edit/", views.ProfileUpdateView.as_view(), name="profile_edit"),
    path("withdraw/", views.WithdrawView.as_view(), name="withdraw"),
    path("admin-list/", views.MemberListView.as_view(), name="member_list"),
    path("<int:pk>/toggle-active/", views.ToggleActiveView.as_view(), name="toggle_active"),
]
