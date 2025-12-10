from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel


class StudyGroup(TimeStampedModel):
    class StudyGroupStatusChoices(models.TextChoices):
        PENDING = "PENDING"
        ONGOING = "ONGOING"
        ENDED = "ENDED"

    name = models.CharField(max_length=20, unique=True)
    introduction = models.CharField(max_length=500, blank=True, null=True)
    max_headcount = models.SmallIntegerField()
    profile_img_url = models.URLField(blank=True, null=True)
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    status = models.CharField(
        choices=StudyGroupStatusChoices.choices,
        max_length=8,
        default=StudyGroupStatusChoices.PENDING,
    )

    class Meta:
        db_table = "study_groups"
        constraints = [
            models.CheckConstraint(
                check=models.Q(max_headcount__gte=1, max_headcount__lte=10),
                name="check_study_group_max_headcount_range",
            )
        ]
        indexes = [
            models.Index(fields=["name"], name="idx_study_group_name"),
            models.Index(fields=["status"], name="idx_study_group_status"),
        ]
        ordering = ["-created_at", "-id"]

    def __str__(self) -> str:
        return self.name


class GroupMember(TimeStampedModel):
    study_group = models.ForeignKey(
        "study_groups.StudyGroup",
        on_delete=models.CASCADE,
        db_column="study_group_id",
        related_name="members",
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, db_column="user_id")
    is_leader = models.BooleanField(default=False)

    class Meta:
        db_table = "study_members"

    def __str__(self) -> str:
        return f"{self.study_group.name} - {self.user}"


class StudyLecture(TimeStampedModel):
    lecture = models.ForeignKey("lectures.CrawledLecture", on_delete=models.CASCADE, db_column="lecture_id")
    study_group = models.ForeignKey("study_groups.StudyGroup", on_delete=models.CASCADE, db_column="study_group_id")

    class Meta:
        db_table = "study_lectures"
