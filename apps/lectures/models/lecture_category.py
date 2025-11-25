from django.db import models

from apps.lectures.models import CrawledLecture
from apps.lectures.models.category import Category


class LectureCategory(models.Model):
    pk = models.CompositePrimaryKey("lecture_id", "category_id", help_text="복합키")
    lecture = models.ForeignKey(CrawledLecture, on_delete=models.CASCADE, help_text="강의 id")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, help_text="카테고리 id")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["pk"]
        db_table = "lecture_categories"

    def __str__(self) -> str:
        return f"[{self.lecture}] {self.category}"
