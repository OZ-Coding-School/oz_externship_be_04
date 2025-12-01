from django.db import models

from apps.core.models import TimeStampedModel
from apps.users.models.users import User


class SocialUser(TimeStampedModel):
    class ProviderChoices(models.TextChoices):
        KAKAO = "kakao", "카카오"
        NAVER = "naver", "네이버"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="social_accounts")
    provider = models.CharField(max_length=20, choices=ProviderChoices.choices)
    provider_id = models.CharField(max_length=255)

    class Meta:
        db_table = "social_users"
        unique_together = ("provider", "provider_id")
