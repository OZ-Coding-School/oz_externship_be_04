from django.db import models

from apps.core.models import TimeStampedModel

from .study_note import StudyNote


class StudyNoteImage(TimeStampedModel):
    """노트에 첨부된 이미지"""

    study_note = models.ForeignKey(
        StudyNote,
        on_delete=models.CASCADE,
        related_name="images",
        db_column="study_note_id",
    )
    img_url = models.URLField()

    class Meta:
        db_table = "study_note_images"
        ordering = ["-created_at", "-id"]
        indexes = [models.Index(fields=["study_note"], name="idx_note_image_note")]

    def __str__(self) -> str:
        return f"{self.study_note} - {self.img_url}"
