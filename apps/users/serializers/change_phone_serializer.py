from typing import Any

from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.users.serializers.verification_serializer import SMSValidator

User = get_user_model()


class ChangePhoneSerializer(serializers.Serializer[Any]):
    phone_number = serializers.CharField(
        required=True, max_length=20, error_messages={"required": "휴대폰 번호를 입력해주세요."}
    )
    code = serializers.CharField(required=True, min_length=6, max_length=6)

    def validate_phone_number(self, value: str) -> str:
        return SMSValidator.phone_unique(self, value)

    def validate_code(self, value: str) -> str:
        return SMSValidator.code_digit(value)
