from django.db import models

from apps.core.models import BaseModel


class Category(BaseModel):
    name = models.CharField(max_length=255, unique=True, help_text="카테고리명")

    class Meta:
        ordering = ["name"]
        db_table = "categories"

    def __str__(self) -> str:
        return self.name


class LectureCategory(BaseModel):
    pk = models.CompositePrimaryKey("lecture_id", "category_id")
    lecture = models.ForeignKey(
        "lectures.CrawledLecture", on_delete=models.CASCADE, related_name="lecture_categories", help_text="강의 id"
    )
    category = models.ForeignKey(
        "lectures.Category", on_delete=models.CASCADE, related_name="category_lectures", help_text="카테고리 id"
    )

    class Meta:
        ordering = ["pk"]
        db_table = "lecture_categories"

    def __str__(self) -> str:
        return f"[{self.lecture}] {self.category}"


class UserPreferCategory(BaseModel):
    pk = models.CompositePrimaryKey("user_id", "category_id")
    user = models.ForeignKey(
        "users.User", on_delete=models.CASCADE, related_name="preferred_categories", help_text="유저 id"
    )
    category = models.ForeignKey(
        "lectures.Category", on_delete=models.CASCADE, related_name="preferred_by_users", help_text="카테고리 id"
    )

    class Meta:
        ordering = ["pk"]
        db_table = "user_prefer_categories"

    def __str__(self) -> str:
        return f"[{self.user}] {self.category}"
