from typing import Any

from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.users.serializers.verification_serializer import SMSValidator

User = get_user_model()


class FindEmailVerifySerializer(serializers.Serializer[Any]):
    phone_number = serializers.CharField(
        required=True, max_length=20, error_messages={"required": "휴대폰 번호를 입력해주세요."}
    )
    code = serializers.CharField(
        required=True, min_length=6, max_length=6, error_messages={"required": "인증 코드를 입력해주세요."}
    )

    def validate_phone_number(self, value: str) -> str:
        return SMSValidator.phone_format(value)

    def validate_code(self, value: str) -> str:
        if not value.isdigit():
            raise serializers.ValidationError("인증 코드는 숫자만 입력 가능합니다.")
        return value


class FindEmailSMSSendSerializer(serializers.Serializer[Any]):
    name = serializers.CharField(required=True, max_length=20, error_messages={"required": "이름을 입력해주세요."})
    phone_number = serializers.CharField(
        required=True, max_length=20, error_messages={"required": "휴대폰 번호를 입력해주세요."}
    )

    def validate_phone_number(self, value: str) -> str:
        return SMSValidator.phone_format(value)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        name = attrs.get("name")
        phone_number = attrs.get("phone_number")

        if not User.objects.filter(name=name, phone_number=phone_number).exists():
            raise serializers.ValidationError("등록된 정보가 없습니다.")

        return attrs
