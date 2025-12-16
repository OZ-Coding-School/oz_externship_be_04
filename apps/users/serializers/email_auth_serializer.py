from typing import Any

from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.users.utils.auth_code import AuthCodeCache

User = get_user_model()


class EmailSignUpSerializer(serializers.Serializer[Any]):
    email = serializers.EmailField(required=True)

    def validate_email(self, value: str) -> str:
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("이미 가입되어 있는 이메일 입니다.")
        return value


class EmailSignUpVerifySerializer(serializers.Serializer[Any]):
    email = serializers.EmailField(required=True)
    code = serializers.CharField(required=True)

    def validate(self, data: Any) -> Any:
        email = data["email"]
        code = data["code"]
        key = f"email:signup:{email}"

        if not AuthCodeCache.verify(key, code):
            raise serializers.ValidationError({"code": ["인증 코드가 올바르지 않거나 만료되었습니다."]})
        return data
