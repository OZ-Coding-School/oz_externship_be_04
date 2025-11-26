from django.db import models

from apps.core.models import TimeStampedModel


class Category(TimeStampedModel):
    name = models.CharField(max_length=255, unique=True, help_text="카테고리명")

    class Meta:
        ordering = ["name"]
        db_table = "categories"

    def __str__(self) -> str:
        return self.name
