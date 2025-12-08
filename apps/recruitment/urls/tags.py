from django.urls import path

from apps.recruitment.views.tags_view import TagListAPIView

urlpatterns = [
    path("/recruitment-tags", TagListAPIView.as_view(), name="tag-list"),
]