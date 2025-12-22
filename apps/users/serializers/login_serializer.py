from typing import Any

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from rest_framework import serializers

User = get_user_model()


class LoginSerializer(serializers.Serializer[Any]):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)

    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        email = data.get("email")
        password = data.get("password")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("가입이되어있지않은 이메일입니다.")

        if not check_password(password, user.password):
            raise serializers.ValidationError("비밀번호가 일치하지 않습니다")

        if not user.is_active == True:
            raise serializers.ValidationError("탈퇴 처리된 유저입니다. 회원 복구를 진행합니다.")

        data["user"] = user
        return data
