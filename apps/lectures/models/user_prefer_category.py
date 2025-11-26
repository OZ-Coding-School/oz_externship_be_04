from django.db import models

from apps.core.models import TimeStampedModel
from apps.lectures.models.category import Category
from apps.users.models import User


class UserPreferCategory(TimeStampedModel):
    pk = models.CompositePrimaryKey("user_id", "category_id", help_text="복합 pk키")
    user = models.ForeignKey(User, on_delete=models.CASCADE, help_text="유저 id")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, help_text="카테고리 id")

    class Meta:
        ordering = ["pk"]
        db_table = "user_prefer_categories"

    def __str__(self) -> str:
        return f"[{self.user}] {self.category}"
