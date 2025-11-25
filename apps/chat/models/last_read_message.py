from django.db import models
from django.db.models import UniqueConstraint

from apps.core.models import TimeStampedModel
from apps.study_groups.models import StudyGroup
from apps.users.models import User


class LastReadMessage(TimeStampedModel):
    study_group = models.ForeignKey(
        StudyGroup,
        on_delete=models.CASCADE,
        related_name="last_read_messages"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="last_read_messages"
    )
    message_id = models.PositiveIntegerField()

    class Meta:
        db_table = "last_read_messages"
        constraints = [
            UniqueConstraint(fields=['study_group', 'user'], name='unique_user_per_study_group')
        ]
