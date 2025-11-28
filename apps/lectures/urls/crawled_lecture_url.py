from django.urls import path

from apps.lectures.views.crawled_lecture_view import CrawledLectureListAPIView

urlpatterns = [
    path("lectures", CrawledLectureListAPIView.as_view(), name="lectures"),
]
