from typing import Any

from django.db import models

from apps.core.models import TimeStampedModel
from apps.users.models.users import User


# 스터디 그룹
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
                check=models.Q(max_headcount__gte=2, max_headcount__lte=10),
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


# 그룹 멤버
class GroupMember(TimeStampedModel):
    study_group_id = models.ForeignKey(
        "study_groups.StudyGroup",
        on_delete=models.CASCADE,
        db_column="study_group_id",
        related_name="groupmember_study_groups",
    )
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name="groupmember_users")
    is_leader = models.BooleanField(default=False)

    class Meta:
        db_table = "study_members"

    def __str__(self) -> str:
        return f"{self.study_group_id.name}의 멤버 {self.user_id.nickname}"


class StudyLecture(TimeStampedModel):
    lecture = models.ForeignKey(
        "lectures.CrawledLecture",
        on_delete=models.CASCADE,
        db_column="lecture_id",
        related_name="studylecture_lectures",
    )
    study_group = models.ForeignKey(
        "study_groups.StudyGroup",
        on_delete=models.CASCADE,
        db_column="study_group_id",
        related_name="studylecture_study_groups",
    )

    class Meta:
        db_table = "study_lectures"
