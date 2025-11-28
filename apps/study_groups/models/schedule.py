from django.db import models

from apps.core.models import TimeStampedModel


class GroupSchedule(TimeStampedModel):
    study_group = models.ForeignKey(
        "study_groups.StudyGroup",
        on_delete=models.CASCADE,
        related_name="schedules",
        db_column="study_group_id",
        help_text="스터디 그룹",
    )
    title = models.CharField(max_length=100, help_text="스케줄 제목")
    objective = models.CharField(max_length=500, blank=True, null=True, help_text="스케줄 설명")
    session_date = models.DateTimeField(help_text="스케줄 날짜")
    start_time = models.TimeField(help_text="시작 시간")
    end_time = models.TimeField(help_text="종료 시간")

    class Meta:
        db_table = "group_schedules"

    def __str__(self) -> str:
        return self.title


class ScheduleParticipants(TimeStampedModel):

    schedule = models.ForeignKey(
        GroupSchedule,
        on_delete=models.CASCADE,
        related_name="participants",
        db_column="schedule_id",
        help_text="스케줄",
    )
    member = models.ForeignKey(
        "study_groups.GroupMember",
        on_delete=models.CASCADE,
        related_name="participants",
        db_column="member_id",
        help_text="참가 맴버",
    )

    class Meta:
        db_table = "schedule_participants"

    def __str__(self) -> str:
        return f"{self.schedule} - {self.member}"
