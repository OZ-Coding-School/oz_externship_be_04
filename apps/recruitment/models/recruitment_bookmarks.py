
from django.db import models

from apps.core.models import TimeStampedModel


class RecruitmentBookmarks(TimeStampedModel):
    # 구인공고 북마크

    recruitment_id = models.ForeignKey(
        "recruitment.Recruitment",
        null=False,
        on_delete=models.CASCADE,
        db_column="recruitment_id",
        related_name="recruitment_bookmarks",
        help_text="공고 ID",
    )
    user_id = models.ForeignKey(
        "users.User",
        null=False,
        on_delete=models.CASCADE,
        db_column="user_id",
        related_name="recruitment_bookmarks",
        help_text="북마크한 유저의 ID",
    )

    class Meta:
        db_table = "recruitment_bookmarks"
        constraints = [
            models.UniqueConstraint(
                fields=["user_id", "recruitment_id"],
                name="pk_user_recruitment_bookmark",
            ),
        ]
        indexes = [models.Index(fields=["user_id"]), models.Index(fields=["recruitment_id"])]

    def __str__(self) -> str:
        return f"{self.user_id} bookmarked {self.recruitment_id}"
