from django.db import models

from apps.core.models import TimeStampedModel
from .study_note import StudyNote


class StudyNoteAttachment(TimeStampedModel):
    """노트에 첨부된 파일"""

    study_note = models.ForeignKey(
        StudyNote,
        on_delete=models.CASCADE,
        related_name="attachments",
        db_column="study_note_id",
    )
    file_url = models.URLField(unique=True)
    file_name = models.CharField(max_length=255)

    class Meta:
        db_table = "study_note_attachments"
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["study_note"], name="idx_note_attachment_note"),
        ]

    def __str__(self) -> str:
        return f"{self.study_note_id} - {self.file_name}"
