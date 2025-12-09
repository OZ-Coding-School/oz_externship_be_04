from django.urls import path

from apps.recruitment.views.recruitment_bookmarks import (
    RecruitmentBookmarkCreateView,
    RecruitmentBookmarkDeleteView,
    RecruitmentBookmarkListView,
)

urlpatterns = [
    # 북마크 목록 조회
    path("/recruitment-bookmarks", RecruitmentBookmarkListView.as_view(), name="recruitment-bookmark-list"),
    # 북마크 추가
    path("/recruitment-bookmarks", RecruitmentBookmarkCreateView.as_view(), name="recruitment-bookmark-create"),
    # 북마크 삭제 (명세서 대로 bookmark ID 사용)
    path(
        "/recruitment-bookmarks/<int:bookmark_id>",
        RecruitmentBookmarkDeleteView.as_view(),
        name="recruitment-bookmark-delete",
    ),
]
