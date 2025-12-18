import uuid
from typing import Any, Dict, Tuple

from django.db import transaction

from apps.users.models.social_user import ProviderChoices, SocialUser
from apps.users.models.users import User


class SocialLoginService:
    @transaction.atomic
    def login_or_signup(self, provider: str, user_info: Dict[str, Any]) -> Tuple[User, bool]:
        provider_id: str = user_info["provider_id"]
        email_input = user_info.get("email")  # Optional[str]
        nickname_input = user_info.get("nickname")  # Optional[str]
        profile_img_url_input = user_info.get("profile_img_url")  # Optional[str]
        gender_input = user_info.get("gender")  # Optional[str]
        phone_number_input = user_info.get("phone_number")  # Optional[str]
        name_input = user_info.get("name")
        birthday_input = user_info.get("birthday")

        if provider not in ProviderChoices.values:
            raise ValueError("유효하지 않은 소셜 로그인 제공자입니다.")

        social_user = (
            SocialUser.objects.filter(provider=provider, provider_id=provider_id).select_related("user").first()
        )

        if social_user:
            return social_user.user, False

        # email 기반 기존 유저 연결
        if email_input:
            existing_user = User.objects.filter(email=email_input).first()
            if existing_user:
                SocialUser.objects.get_or_create(
                    user=existing_user,
                    provider=provider,
                    provider_id=provider_id,
                )

                if not existing_user.nickname and nickname_input:
                    existing_user.nickname = nickname_input

                if not existing_user.profile_img_url and profile_img_url_input:
                    existing_user.profile_img_url = profile_img_url_input

                # gender, phone_number도 조건 체크 후 할당
                if not existing_user.gender and gender_input:
                    existing_user.gender = gender_input
                if not existing_user.phone_number and phone_number_input:
                    existing_user.phone_number = phone_number_input
                if not existing_user.name and name_input:
                    existing_user.name = name_input
                if not existing_user.birthday and birthday_input:
                    existing_user.birthday = birthday_input

                existing_user.save()
                return existing_user, False

        # 새 이메일 생성
        email = email_input or f"{provider}_{provider_id}@auto.com"
        final_nickname = nickname_input
        if not final_nickname:
            final_nickname = self._generate_unique_nickname(provider)
        else:
            # 소셜 닉네임이 이미 DB에 있다면? -> 뒤에 난수 붙여서 충돌 방지
            while User.objects.filter(nickname=final_nickname).exists():
                final_nickname = f"{nickname_input}_{uuid.uuid4().hex[:4]}"

        # 기본 user data
        user_data: Dict[str, Any] = {
            "email": email,
            "nickname": final_nickname,
            "name": name_input or final_nickname,
            "birthday": birthday_input,
            "is_active": True,
            "profile_img_url": profile_img_url_input or "",
        }

        # Optional 필드는 있을 때만 넣기 → mypy 해결
        if gender_input is not None:
            user_data["gender"] = gender_input

        if phone_number_input is not None:
            user_data["phone_number"] = phone_number_input

        new_user = User.objects.create(**user_data)

        SocialUser.objects.create(
            user=new_user,
            provider=provider,
            provider_id=provider_id,
        )

        return new_user, True

    def _generate_unique_nickname(self, provider: str) -> str:
        return f"{provider}_{uuid.uuid4().hex[:8]}"
