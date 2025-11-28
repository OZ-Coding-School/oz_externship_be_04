from typing import Any, Dict

from rest_framework import serializers

from apps.users.models.social_user import SocialUser
from apps.users.models.users import User


class KakaoLoginSerializer(serializers.Serializer[Dict[str, Any]]):
    access_token = serializers.CharField()

    def create_user(self, data: Dict[str, Any]) -> User:
        provider_id = data["provider_id"]
        nickname = data.get("nickname", "user")

        user, _ = User.objects.get_or_create(
            nickname=nickname,
            defaults={"email": "", "is_active": True},
        )
        SocialUser.objects.get_or_create(
            user=user,
            provider="kakao",
            provider_id=provider_id,
        )
        return user
