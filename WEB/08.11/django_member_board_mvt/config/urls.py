"""프로젝트 최상위 URL 라우팅 설정입니다."""
# Django 관리자 사이트 객체를 가져옵니다.
from django.contrib import admin
# include()로 앱 URL을 연결하고 path()로 URL 패턴을 정의합니다.
from django.urls import include, path
# 개발 중 업로드 파일을 Django 개발 서버로 제공하기 위한 함수를 가져옵니다.
from django.conf.urls.static import static
# settings의 DEBUG, MEDIA_URL, MEDIA_ROOT 값을 참조합니다.
from django.conf import settings
# 메인 화면 View 함수를 가져옵니다.
from members.views import home

# 브라우저 요청 URL을 각 View 또는 앱 URL 설정으로 연결합니다.
urlpatterns = [
    # Django 기본 관리자 사이트입니다.
    path("admin/", admin.site.urls),
    # 사이트 첫 화면입니다.
    path("", home, name="home"),
    # /members/ 이하 요청을 회원 앱 URL 설정으로 전달합니다.
    path("members/", include("members.urls")),
    # /boards/ 이하 요청을 게시판 앱 URL 설정으로 전달합니다.
    path("boards/", include("boards.urls")),
]

# DEBUG=True인 개발 환경에서는 /media/ URL로 업로드 파일을 직접 확인할 수 있게 합니다.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
