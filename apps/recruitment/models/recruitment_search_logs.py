
from django.db import models

from apps.core.models import TimeStampedModel


class RecruitmentSearchLogs(TimeStampedModel):
    # 공고 검색 기록

    user_id = models.ForeignKey(
        "users.User",
        null=False,
        on_delete=models.CASCADE,
        db_column="user_id",
        related_name="recruitment_search_logs",
        help_text="유저 ID",
    )
    keyword = models.CharField(max_length=255, null=False, blank=False, help_text="검색어")

    class Meta:
        db_table = "recruitment_search_logs"
        indexes = [models.Index(fields=["keyword"]), models.Index(fields=["created_at"])]

    def __str__(self) -> str:
        return f"{self.user_id} - {self.keyword} - {self.created_at:%Y-%m-%d %H:%M:%S}"
