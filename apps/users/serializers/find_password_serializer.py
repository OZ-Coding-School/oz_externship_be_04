from typing import Any, cast

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework.request import Request


class PasswordResetSerializer(serializers.Serializer[Any]):
    token = serializers.CharField(
        required=False,
        max_length=64,
        error_messages={"required": "토큰을 입력해주세요."},
    )

    new_password = serializers.CharField(
        required=True,
        min_length=8,
        max_length=128,
        error_messages={
            "required": "이 필드는 필수 항목입니다.",
            "min_length": "비밀번호는 8자 이상이어야 합니다.",
        },
    )

    def validate_new_password(self, value: str) -> str:
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.messages)

        return value


class PasswordChangeSerializer(serializers.Serializer[Any]):
    current_password = serializers.CharField(
        required=True, error_messages={"required": "현재 비밀번호를 입력해주세요."}
    )

    new_password = serializers.CharField(
        required=True,
        min_length=8,
        max_length=128,
        error_messages={
            "required": "새 비밀번호를 입력해주세요.",
            "min_length": "비밀번호는 8자 이상이어야 합니다.",
        },
    )

    confirm_password = serializers.CharField(
        required=True, error_messages={"required": "비밀번호 확인을 입력해주세요."}
    )

    def validate_current_password(self, value: str) -> str:
        request = cast(Request, self.context.get("request"))
        user = request.user

        if not user.check_password(value):
            raise serializers.ValidationError("현재 비밀번호가 일치하지 않습니다.")

        return value

    def validate_new_password(self, value: str) -> str:
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.messages)

        return value

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        new_password = attrs.get("new_password")
        confirm_password = attrs.get("confirm_password")

        if new_password != confirm_password:
            raise serializers.ValidationError({"new_password": ["새 비밀번호가 일치하지 않습니다."]})

        return attrs
