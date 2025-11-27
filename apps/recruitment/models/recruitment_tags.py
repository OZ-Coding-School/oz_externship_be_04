from django.db import models

from apps.core.models import TimeStampedModel


class RecruitmentTag(TimeStampedModel):
    """스터디 구인 공고, 태그 중간 테이블"""

    pk = models.CompositePrimaryKey("recruitment", "tag")

    recruitment = models.ForeignKey(
        "recruitment.Recruitment",
        on_delete=models.CASCADE,
        related_name="recruitment_tags",
        help_text="태그 연결된 구인 공고 ID",
    )

    tag = models.ForeignKey(
        "recruitment.Tag",
        on_delete=models.CASCADE,
        related_name="recruitment_tags",
        help_text="모집 공고에 사용하는 태그 ID",
    )

    class Meta:
        db_table = "recruitment_tags"

    def __str__(self) -> str:
        return f"[{self.recruitment.title}] - Tag: {self.tag.name}"
