import uuid
from typing import Any, Dict, Tuple, Optional
from django.db import transaction

from apps.users.models.social_user import ProviderChoices, SocialUser
from apps.users.models.users import User


class SocialLoginService:
    @transaction.atomic
    def login_or_signup(self, provider: str, user_info: Dict[str, Any]) -> Tuple[User, bool]:
        provider_id: str = user_info["provider_id"]

        email_input: Optional[str] = user_info.get("email")
        nickname_input: Optional[str] = user_info.get("nickname")
        profile_img_url_input: Optional[str] = user_info.get("profile_img_url")
        gender_input: Optional[str] = self._normalize_gender(user_info.get("gender"))
        phone_number_input: Optional[str] = user_info.get("phone_number")

        if provider not in ProviderChoices.values:
            raise ValueError("유효하지 않은 소셜 로그인 제공자입니다.")

        social_user: Optional[SocialUser] = (
            SocialUser.objects.filter(provider=provider, provider_id=provider_id)
            .select_related("user")
            .first()
        )
        if social_user:
            return social_user.user, False

        if email_input:
            existing_user: Optional[User] = User.objects.filter(email=email_input).first()
            if existing_user:

                SocialUser.objects.create(
                    user=existing_user,
                    provider=provider,
                    provider_id=provider_id,
                )

                if nickname_input:
                    existing_user.nickname = self._safe_nickname(nickname_input)

                if profile_img_url_input:
                    existing_user.profile_img_url = profile_img_url_input

                if gender_input is not None:
                    existing_user.gender = gender_input

                if phone_number_input is not None:
                    existing_user.phone_number = phone_number_input

                existing_user.save()
                return existing_user, False

        email: str = email_input or f"{provider}_{provider_id}@auto.com"
        base_nickname: str = nickname_input or f"{provider}_{uuid.uuid4().hex[:6]}"
        nickname: str = self._safe_nickname(base_nickname)

        user_data: Dict[str, Any] = {
            "email": email,
            "nickname": nickname,
            "name": nickname,
            "is_active": True,
            "profile_img_url": profile_img_url_input or "",
        }

        if gender_input is not None:
            user_data["gender"] = gender_input

        if phone_number_input is not None:
            user_data["phone_number"] = phone_number_input

        user: User = User.objects.create(**user_data)

        SocialUser.objects.create(
            user=user,
            provider=provider,
            provider_id=provider_id,
        )

        return user, True

    def _safe_nickname(self, base: str) -> str:
        nickname: str = base
        suffix: int = 1
        while User.objects.filter(nickname=nickname).exists():
            nickname = f"{base}_{suffix}"
            suffix += 1
        return nickname

    def _normalize_gender(self, gender: Any) -> Optional[str]:
        if gender is None:
            return None

        gender_str: str = str(gender).lower()

        if gender_str in ("m", "male"):
            return "M"
        if gender_str in ("f", "female"):
            return "F"

        return None
