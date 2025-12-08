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
        nickname: str | None = user_info.get("nickname")
        profile_img_url: str | None = user_info.get("profile_img_url")
        gender: str | None = user_info.get("gender")
        phone_number: str | None = user_info.get("phone_number")

        if provider not in ProviderChoices.values:
            raise ValueError("유효하지 않은 소셜 로그인 제공자입니다.")

        social_user = (
            SocialUser.objects.filter(provider=provider, provider_id=provider_id).select_related("user").first()
        )
        if social_user:
            return social_user.user, False

        if email:
            existing_user = User.objects.filter(email=email).first()
            if existing_user:
                SocialUser.objects.create(
                    user=existing_user,
                    provider=provider,
                    provider_id=provider_id,
                )

                if nickname and existing_user.nickname != nickname:
                    existing_user.nickname = nickname
                if profile_img_url:
                    existing_user.profile_img_url = profile_img_url
                existing_user.save()

                return existing_user, False

        if not email:
            email = f"{provider}_{provider_id}@auto.com"

        if not nickname:
            nickname = self._generate_unique_nickname(provider)

        new_user = User.objects.create(
            email=email,
            nickname=nickname,
            name=nickname,
            is_active=True,
            profile_img_url=profile_img_url or "",
            gender=gender,
            phone_number=phone_number,
        )

        SocialUser.objects.create(
            user=new_user,
            provider=provider,
            provider_id=provider_id,
        )

        return new_user, True

    def _generate_unique_nickname(self, provider: str) -> str:
        return f"{provider}_{uuid.uuid4().hex[:8]}"
