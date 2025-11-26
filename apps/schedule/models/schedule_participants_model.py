from django.db import models

from ...core.models import TimeStampedModel


class ScheduleParticipantsModel(TimeStampedModel):

    schedule = models.ForeignKey(
        "group_schedules",
        on_delete=models.CASCADE,
        related_name="participants",
        db_column="schedule_id",
        help_text="스케줄",
    )
    member = models.ForeignKey(
        "group_members",
        on_delete=models.CASCADE,
        related_name="participants",
        db_column="member_id",
        help_text="참가 맴버",
    )

    class Meta:
        db_table = "schedule_participants"

    def __str__(self) -> str:
        return f"{self.schedule_id} - {self.member_id}"
