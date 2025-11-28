from typing import Any, Dict

from rest_framework import serializers

from apps.users.models.users import SocialUser, User


class KakaoOAuthSerializer(serializers.Serializer):
    provider_id = serializers.CharField()
    nickname = serializers.CharField(required=False)
    profile_image = serializers.URLField(required=False)

    def create(self, validated_data: Dict[str, Any]) -> User:
        # user 생성 로직은 service로 이동 (여긴 시리얼라이저만!)
        return super().create(validated_data)
