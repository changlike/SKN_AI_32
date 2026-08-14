from django.urls import path
from . import api_views

urlpatterns = [
    path("", api_views.BoardListAPIView.as_view(), name="api_list"),
    path("create/", api_views.BoardCreateAPIView.as_view(), name="api_create"),
    path("<int:pk>/", api_views.BoardDetailAPIView.as_view(), name="api_detail"),
    path("<int:pk>/update/", api_views.BoardUpdateAPIView.as_view(), name="api_update"),
    path("<int:pk>/delete/", api_views.BoardDeleteAPIView.as_view(), name="api_delete"),
]
