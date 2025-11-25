from django.db import models

from apps.lectures.models.category import Category
from apps.users.models import Users


class UserPreferCategory(models.Model):
    pk = models.CompositePrimaryKey("user_id", "category_id", help_text="복합 pk키")
    user = models.ForeignKey(Users, on_delete=models.CASCADE, help_text="유저 id")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, help_text="카테고리 id")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["pk"]
        db_table = "user_prefer_categories"

    def __str__(self) -> str:
        return f"[{self.user}] {self.category}"
