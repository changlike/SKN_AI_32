from django.urls import path
from . import api_views

urlpatterns = [
    path("csrf/", api_views.CsrfView.as_view(), name="api_csrf"),
    path("session/", api_views.SessionView.as_view(), name="api_session"),
    path("signup/", api_views.SignUpAPIView.as_view(), name="api_signup"),
    path("login/", api_views.LoginAPIView.as_view(), name="api_login"),
    path("logout/", api_views.LogoutAPIView.as_view(), name="api_logout"),
    path("profile/", api_views.ProfileAPIView.as_view(), name="api_profile"),
    path("withdraw/", api_views.WithdrawAPIView.as_view(), name="api_withdraw"),
    path("admin-list/", api_views.MemberListAPIView.as_view(), name="api_member_list"),
    path("<int:pk>/toggle-active/", api_views.ToggleActiveAPIView.as_view(), name="api_toggle_active"),
]
