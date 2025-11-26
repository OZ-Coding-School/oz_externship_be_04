from django.conf import settings
from django.db import models

from apps.lectures.models import CrawledLecture


class LectureBookmark(models.Model):

    pk = models.CompositePrimaryKey("user", "lecture")

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="lecture_bookmarks")
    lecture = models.ForeignKey(CrawledLecture, on_delete=models.CASCADE, related_name="bookmarks")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "lecture_bookmarks"
        ordering = ["-created_at", "-updated_at"]



        def __str__(self):
            return f"LectureBookmark(user_id={self.user_id}, lecture_id={self.lecture_id})"