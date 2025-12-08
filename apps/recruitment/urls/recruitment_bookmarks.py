from django.urls import path

from apps.recruitment.views.recruitment_bookmarks import (
    RecruitmentBookmarkDeleteAPIView,
    RecruitmentBookmarkListCreateAPIView,
)

urlpatterns = [
    path("/recruitment-bookmarks", RecruitmentBookmarkListCreateAPIView.as_view(), name="recruitment-bookmark-list"),
    path(
        "/recruitment-bookmarks/<uuid:recruitment_uuid>",
        RecruitmentBookmarkDeleteAPIView.as_view(),
        name="recruitment-bookmark-delete",
    ),
]
