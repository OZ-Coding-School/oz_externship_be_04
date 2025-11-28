from rest_framework import serializers
from django.contrib.auth import get_user_model
from apps.users.models import SocialAccount

User = get_user_model()


class SocialLoginSerializer(serializers.Serializer):
    provider = serializers.CharField()
    provider_id = serializers.CharField()
    nickname = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    profile_image = serializers.URLField(required=False, allow_null=True)

    def _generate_unique_nickname(self, base_nickname: str) -> str:
        nickname = base_nickname
        counter = 1

        while User.objects.filter(nickname=nickname).exists():
            nickname = f"{base_nickname}{counter}"
            counter += 1

        return nickname

    def create(self, validated_data):
        provider = validated_data["provider"]
        provider_id = validated_data["provider_id"]
        nickname = validated_data.get("nickname")
        profile_image = validated_data.get("profile_image")

        try:
            social_account = SocialAccount.objects.get(provider=provider, provider_id=provider_id)
            user = social_account.user
            return user

        except SocialAccount.DoesNotExist:
            if not nickname:
                nickname = f"user{provider_id}"

            nickname = self._generate_unique_nickname(nickname)

            user = User.objects.create(
                nickname=nickname,
                profile_img_url=profile_image or "",
                is_active=True,
            )

            SocialAccount.objects.create(
                user=user,
                provider=provider,
                provider_id=provider_id,
            )

            return user
