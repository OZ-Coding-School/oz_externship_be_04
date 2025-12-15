# mypy: ignore-errors
from typing import Any, Dict
from rest_framework import serializers


class SocialLoginSerializer(serializers.Serializer):
    provider = serializers.CharField()
    provider_id = serializers.CharField()
    email = serializers.EmailField(required=False, allow_null=True, allow_blank=True)
    nickname = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    profile_img_url = serializers.URLField(required=False, allow_blank=True, allow_null=True)
    gender = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    phone_number = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        if not attrs.get("provider"):
            raise serializers.ValidationError({"provider": "provider 필수"})
        if not attrs.get("provider_id"):
            raise serializers.ValidationError({"provider_id": "provider_id 필수"})
        return attrs
