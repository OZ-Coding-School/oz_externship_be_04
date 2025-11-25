from apps.core.models import TimeStampedModel
from django.db import models

from apps.study_groups.models import StudyGroup
from apps.users.models import User


class ChatMessage(TimeStampedModel):
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="chat_messages"
    )
    study_group = models.ForeignKey(
        StudyGroup,
        on_delete=models.CASCADE,
        related_name="chat_messages"
    )
    content = models.CharField(max_length=500)

    class Meta:
        db_table = "chat_messages"
