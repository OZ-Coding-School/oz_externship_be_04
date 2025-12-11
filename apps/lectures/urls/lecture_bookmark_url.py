from django.urls import path

from apps.lectures.views.lecture_bookmark_view import (
    LectureBookmarkDestroyAPIView,
    LectureBookmarkListCreateAPIView,
)

app_name = "lecture_bookmarks"

urlpatterns = [
    path(
        "/lecture-bookmarks",
        LectureBookmarkListCreateAPIView.as_view(),
        name="lecture-bookmark-list-create",
    ),
    path(
        "/lecture-bookmarks/<int:bookmark_id>",
        LectureBookmarkDestroyAPIView.as_view(),
        name="lecture-bookmark-destroy",
    ),
]
