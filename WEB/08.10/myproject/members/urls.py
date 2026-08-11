# members/urls.py
# URL 패턴을 작성하기 위해 path를 가져옵니다.
from django.urls import path
# 같은 앱의 views 모듈을 가져옵니다.
from . import views


# URL namespace 설정
app_name ="members"

urlpatterns = [

    path("signup/", views.signup_view, name="signup"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
]