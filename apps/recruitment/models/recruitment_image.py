from django.db import models

from apps.core.models import TimeStampedModel


class RecruitmentImage(TimeStampedModel):
    """스터디 구인 공고 이미지"""

    recruitment = models.ForeignKey(
        "Recruitment", on_delete=models.CASCADE, related_name="images", db_column="recruitment_id", help_text="구인공고"
    )

    img_url = models.URLField(max_length=500, help_text="이미지 URL")

    class Meta:
        db_table = "recruitment_image"
        indexes = [
            models.Index(fields=["recruitment", "-created_at"], name="idx_recruitment_img_created"),
        ]

    def __str__(self) -> str:
        return f"{self.recruitment.title} - 이미지 {self.img_url}"
