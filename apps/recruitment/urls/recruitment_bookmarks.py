from django.urls import path

from apps.recruitment.views.recruitment_bookmarks import (
    RecruitmentBookmarkDeleteView,
    RecruitmentBookmarkListCreateView,
)

urlpatterns = [
    # 북마크 목록 조회 및 추가 (GET: 목록, POST: 추가)
    path(
        "recruitment-bookmarks/", RecruitmentBookmarkListCreateView.as_view(), name="recruitment-bookmark-list-create"
    ),
    # 북마크 삭제 (DELETE)
    path(
        "recruitment-bookmarks/<int:bookmark_id>/",
        RecruitmentBookmarkDeleteView.as_view(),
        name="recruitment-bookmark-delete",
    ),
]
