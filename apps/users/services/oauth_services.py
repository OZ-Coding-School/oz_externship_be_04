import uuid
from typing import Any, Dict, Tuple

from django.db import transaction

from apps.users.models.social_user import ProviderChoices, SocialUser
from apps.users.models.users import User


class SocialLoginService:
    @transaction.atomic
    def login_or_signup(self, provider: str, user_info: Dict[str, Any]) -> Tuple[User, bool]:
        provider_id: str = user_info["provider_id"]
        email: str | None = user_info.get("email")

        if provider not in ProviderChoices.values:
            raise ValueError("유효하지 않은 소셜 로그인 제공자입니다.")

        social_user: SocialUser | None = (
            SocialUser.objects.filter(provider=provider, provider_id=provider_id).select_related("user").first()
        )

        if social_user:
            return social_user.user, False

        if email:
            existing_user: User | None = User.objects.filter(email=email).first()
            if existing_user:
                SocialUser.objects.create(
                    user=existing_user,
                    provider=provider,
                    provider_id=provider_id,
                )
                return existing_user, False

        if not email:
            email = f"{provider}_{provider_id}@auto.com"

        nickname = self._generate_unique_nickname()

        user: User = User.objects.create(
            email=email,
            nickname=nickname,
            name=nickname,
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
