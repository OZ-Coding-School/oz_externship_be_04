from django.urls import path

from apps.lectures.views.bookmark_lecture_view import LectureBookmarkIdListAPIView
from apps.lectures.views.lecture_bookmark_view import (
    LectureBookmarkDestroyAPIView,
    LectureBookmarkListCreateAPIView,
)

app_name = "lecture_bookmarks"

urlpatterns = [
    path(
        "/lecture-bookmarks/",
        LectureBookmarkListCreateAPIView.as_view(),
        name="lecture-bookmark-list-create",
    ),
    path(
        "/lecture-bookmarks/<int:lecture_id>/",
        LectureBookmarkDestroyAPIView.as_view(),
        name="lecture-bookmark-destroy",
    ),
    path(
        "/lecture-bookmarks/ids/",
        LectureBookmarkIdListAPIView.as_view(),
        name="lecture-bookmark-id-list",
    ),
]