from django.urls import include, path
from .api_views import HomeAPIView

urlpatterns = [
    path("home/", HomeAPIView.as_view(), name="api_home"),
    path("members/", include("members.api_urls")),
    path("boards/", include("boards.api_urls")),
    path("ai/", include("rag.api_urls")),
]
