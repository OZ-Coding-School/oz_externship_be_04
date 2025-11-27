from django.db import models

from apps.core.models import TimeStampedModel


class Tag(TimeStampedModel):
    """스터디 구인 공고 사용자 정의 태그"""

    name = models.CharField(max_length=20, unique=True, help_text="태그 이름")

    class Meta:
        db_table = "tags"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name