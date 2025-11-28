from rest_framework import serializers

from apps.users.models.social_account import SocialAccount
from apps.users.models.users import SocialUser, User


class SocialLoginSerializer(serializers.Serializer):
    provider = serializers.CharField()
    provider_id = serializers.CharField()
    nickname = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    profile_image = serializers.URLField(required=False, allow_blank=True, allow_null=True)

    def create(self, validated_data):
        provider = validated_data["provider"]
        provider_id = validated_data["provider_id"]

        social_account = (
            SocialAccount.objects.filter(provider=provider, provider_id=provider_id).select_related("user").first()
        )

        if social_account:
            return social_account.user, False

        nickname = validated_data.get("nickname") or "user"
        original_nickname = nickname
        suffix = 1

        while User.objects.filter(nickname=nickname).exists():
            nickname = f"{original_nickname}_{suffix}"
            suffix += 1

        user = User.objects.create(
            email=f"{provider}_{provider_id}@auto.com",
            nickname=nickname,
            name=nickname,
            is_active=True,
        )

        SocialAccount.objects.create(user=user, provider=provider, provider_id=provider_id)

        return user, True
