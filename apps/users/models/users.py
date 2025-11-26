from datetime import timedelta
from typing import Any

from django.contrib.auth.base_user import AbstractBaseUser
from django.db import models
from django.utils import timezone

from apps.core.models import TimeStampedModel
from apps.users.reason_choices import WithdrawalReason


class GenderChoices(models.TextChoices):
    MALE = "M", "남성"
    FEMALE = "F", "여성"


class User(TimeStampedModel, AbstractBaseUser):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=30)
    nickname = models.CharField(max_length=10, unique=True)
    phone_number = models.CharField(max_length=20, unique=True)
    gender = models.CharField(max_length=1, choices=GenderChoices.choices)
    birthday = models.DateField()
    profile_img_url = models.URLField(max_length=255)
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    USERNAME_FIELD = "email"

    class Meta:
        db_table = "users"


class Withdrawal(TimeStampedModel):
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="withdrawals", db_column="user_id"
    )
    reason = models.CharField(
        max_length=100,
        choices=WithdrawalReason.choices,
    )
    reason_detail = models.CharField(max_length=500, blank=True, default="")
    due_date = models.DateField()

    class Meta:
        db_table = "withdrawals"

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self.due_date:
            self.due_date = timezone.now().date() + timedelta(days=14)
        super().save(*args, **kwargs)
