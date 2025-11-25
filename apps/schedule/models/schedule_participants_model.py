from django.db import models

class ScheduleParticipantsModel(models.Model):

    schedule = models.ForeignKey(
        'group_schedules',
        on_delete=models.CASCADE,
        related_name='participants',
        db_column = "schedule_id",
        help_text = '스케줄',
    )
    member = models.ForeignKey(
        'group_members',
        on_delete=models.CASCADE,
        related_name='participants',
        db_column = 'member_id',
        help_text = '참가 맴버',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'schedule_participants'

    def __str__(self) -> str:
        return f'{self.schedule_id} - {self.member_id}'