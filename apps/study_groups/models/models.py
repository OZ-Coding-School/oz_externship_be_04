from django.db import models

from apps.core.models import TimeStampedModel
from apps.users.models.users import User


# 스터디 그룹
class StudyGroup(models.Model):
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
    created_at = models.DateTimeField(auto_now_add=True)  # 처음 생성 시에만 자동 저장
    updated_at = models.DateTimeField(auto_now=True)  # 갱신 시 저장

    class Meta:
        db_table = "study_groups"

    def __str__(self) -> str:
        return self.name


# 그룹 멤버
class GroupMember(TimeStampedModel):
    study_group_id = models.ForeignKey("study_groups.StudyGroup", on_delete=models.CASCADE)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    is_leader = models.BooleanField(default=False)

    class Meta:
        db_table = "study_members"

    def __str__(self) -> str:
        return f"{self.study_group_id.name}의 멤버 {self.user_id.nickname}"
