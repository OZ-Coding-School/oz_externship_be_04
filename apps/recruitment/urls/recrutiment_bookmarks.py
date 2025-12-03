from django.urls import path

from apps.recruitment.views.recruitment_bookmarks import (
    RecruitmentBookmarkCreateAPIView,
    RecruitmentBookmarkDeleteAPIView,
    RecruitmentBookmarkListAPIView,
)

urlpatterns = [
    path("/recruitment-bookmarks", RecruitmentBookmarkCreateAPIView.as_view(), name="recruitment-bookmark-create"),
    path("/recruitment-bookmarks", RecruitmentBookmarkListAPIView.as_view(), name="recruitment-bookmark-list"),
    path(
        "/recruitment-bookmarks/<int:bookmark_id>",
        RecruitmentBookmarkDeleteAPIView.as_view(),
        name="recruitment-bookmark-delete",
    ),
]
