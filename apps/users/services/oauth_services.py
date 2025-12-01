from typing import Dict, Any
from django.db import transaction
from apps.users.models.users import User
from apps.users.models.social_user import SocialUser, ProviderChoices


class SocialLoginService:
    @transaction.atomic
    def login_or_signup(self, provider: str, user_info: Dict[str, Any]) -> tuple[User, bool]:
        provider_id = user_info["provider_id"]
        nickname = user_info.get("nickname", "user")

        social_user = SocialUser.objects.filter(
            provider=provider,
            provider_id=provider_id
        ).select_related("user").first()

        if social_user:
            return social_user.user, False

        user = User.objects.create(
            email=f"{provider}_{provider_id}@auto.com",
            nickname=self._generate_unique_nickname(nickname),
            is_active=True,
        )

        SocialUser.objects.create(
            user=user,
            provider=provider,
            provider_id=provider_id,
        )

        return user, True

    def _generate_unique_nickname(self, base_nickname: str) -> str:
        nickname = base_nickname
        suffix = 1
        while User.objects.filter(nickname=nickname).exists():
            nickname = f"{base_nickname}_{suffix}"
            suffix += 1
        return nickname
