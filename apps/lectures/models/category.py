from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=255, unique=True, help_text="카테고리명")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        db_table = "categories"

    def __str__(self) -> str:
        return self.name
