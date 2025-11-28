from django.urls import path

from apps.lectures.views.crawled_lecture_view import CrawledLectureAVIView

urlpatterns = [
    path("lectures/", CrawledLectureAVIView.as_view(), name="lectures"),
]