from django.urls import path

from apps.recruitment.views.recruitment_tags_view import RecruitmentTagAPIView
from apps.recruitment.views.tags_view import TagListAPIView

urlpatterns = [
    path("recruitment-tags", TagListAPIView.as_view(), name="tag-list"),
    path("recruitment-tags/<uuid:recruitment_uuid>", RecruitmentTagAPIView.as_view(), name="recruitment-tag"),
]
