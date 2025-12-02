from django.urls import path

from apps.lectures.views.admin_crawled_lecture_view import (
    AdminCrawledLectureRetrieveView,
    AdminCrawledLectureView,
)
from apps.lectures.views.crawled_lecture_view import CrawledLectureListAPIView

urlpatterns = [
    path("/lectures", CrawledLectureListAPIView.as_view(), name="lectures"),
    path("/admin/lectures", AdminCrawledLectureView.as_view(), name="admin_crawled_lectures"),
    path(
        "/admin/lectures/<int:lecture_id>",
        AdminCrawledLectureRetrieveView.as_view(),
        name="admin_crawled_lecture_detail",
    ),
]
