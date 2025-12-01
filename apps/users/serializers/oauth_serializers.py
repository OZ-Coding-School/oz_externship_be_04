from typing import Any, Dict

from rest_framework import serializers


class SocialLoginSerializer(serializers.Serializer[Dict[str, Any]]):
    provider = serializers.CharField()
    provider_id = serializers.CharField()
    nickname = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    profile_image = serializers.URLField(required=False, allow_blank=True, allow_null=True)

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        provider = attrs.get("provider")
        provider_id = attrs.get("provider_id")

        if not provider or not provider_id:
            raise serializers.ValidationError("필수 필드 누락")

        return attrs
