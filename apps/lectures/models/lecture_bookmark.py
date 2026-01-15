from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel
from apps.lectures.models import CrawledLecture


class LectureBookmark(TimeStampedModel):

    pk = models.CompositePrimaryKey("user", "lecture")

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="lecture_bookmarks")
    lecture = models.ForeignKey(CrawledLecture, on_delete=models.CASCADE, related_name="bookmarks")

    class Meta:
        db_table = "lecture_bookmarks"
        ordering = ["-created_at", "-updated_at"]

    def __str__(self) -> str:
        return f"LectureBookmark(user_id={self.user}, lecture_id={self.lecture})"
