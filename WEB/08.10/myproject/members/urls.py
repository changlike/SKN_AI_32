# members/urls.py

# URL을 View와 연결하기 위한 path임
from django.urls import path

# 현재 앱의 View 가져옴
from . import views


# URL namespace 설정
app_name = "members"

urlpatterns = [

    # /members/signup/
    path(
        "signup/",
        views.signup_view,
        name="signup",
    ),

    # /members/login/
    path(
        "login/",
        views.login_view,
        name="login",
    ),

    # /members/logout/
    path(
        "logout/",
        views.logout_view,
        name="logout",
    ),
]