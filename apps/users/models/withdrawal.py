from datetime import timedelta
from typing import Any

from django.db import models
from django.utils import timezone

from apps.core.models import TimeStampedModel
from apps.users.models.users import User
from apps.users.utils.reason_choices import WithdrawalReason


class Withdrawal(TimeStampedModel):
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="withdrawals", db_column="user_id"
    )
    reason = models.CharField(
        max_length=100,
        choices=WithdrawalReason.choices,
    )
    reason_detail = models.CharField(max_length=500)
    due_date = models.DateField()
    withdrawn_at = models.DateTimeField()

    class Meta:
        db_table = "withdrawals"

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self.withdrawn_at:
            self.withdrawn_at = timezone.now()
        if not self.due_date:
            self.due_date = self.withdrawn_at.date() + timedelta(days=14)
        super().save(*args, **kwargs)
