import uuid
from typing import Any, Dict

from django.db import transaction

from apps.users.models.social_user import ProviderChoices, SocialUser
from apps.users.models.users import User


class SocialLoginService:
    @transaction.atomic
    def login_or_signup(self, provider: str, user_info: Dict[str, Any]) -> tuple[User, bool]:
        provider_id = user_info["provider_id"]

        if provider not in ProviderChoices.values:
            raise ValueError("유효하지 않은 소셜 로그인 제공자입니다.")

        social_user = (
            SocialUser.objects.filter(provider=provider, provider_id=provider_id).select_related("user").first()
        )

        if social_user:
            return social_user.user, False

        user = User.objects.create(
            email=f"{provider}_{provider_id}@auto.com",
            nickname=self._generate_unique_nickname(),
            is_active=True,
        )

        SocialUser.objects.create(
            user=user,
            provider=provider,
            provider_id=provider_id,
        )

        return user, True

    def _generate_unique_nickname(self) -> str:
        return f"user_{uuid.uuid4().hex[:8]}"
