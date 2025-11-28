from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel
from .study_group import StudyGroup


class StudyNote(TimeStampedModel):
    """스터디 그룹 노트 본문"""

    study_group = models.ForeignKey(
        StudyGroup,
        on_delete=models.CASCADE,
        related_name="notes",
        db_column="study_group_id",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="study_notes",
        db_column="author_id",
    )
    title = models.CharField(max_length=255)
    content = models.TextField()
    ai_summary = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "study_notes"
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["study_group"], name="idx_study_note_group"),
            models.Index(fields=["author"], name="idx_study_note_author"),
        ]

    def __str__(self) -> str:
        return f"{self.title} ({self.study_group})"
