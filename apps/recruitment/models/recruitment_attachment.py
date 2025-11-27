from django.db import models

from apps.core.models import TimeStampedModel


class RecruitmentAttachment(TimeStampedModel):
    """스터디 구인 공고 첨부 파일"""

    recruitment = models.ForeignKey(
        "Recruitment",
        on_delete=models.CASCADE,
        related_name="attachments",
        db_column="recruitment_id",
        help_text="구인공고",
    )

    file_url = models.URLField(max_length=255, unique=True, help_text="S3 등에 업로드된 파일의 URL")

    file_name = models.CharField(max_length=50, help_text="사용자가 업로드한 원본 파일명")

    class Meta:
        db_table = "recruitment_attachments"
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["recruitment", "-created_at"], name="idx_recruitment_created"),
        ]

    def __str__(self) -> str:
        return f"{self.recruitment.title} - {self.file_name}"