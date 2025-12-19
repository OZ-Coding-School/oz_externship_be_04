import re
from typing import Any

from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class SMSValidator:
    REGEX_PHONE = r"^01[0-9]-\d{3,4}-\d{4}$"
    REGEX_PHONE_NO_HYPHEN = r"^01[0-9]\d{8}$"

    @staticmethod
    def phone_format(value: str) -> str:
        if not (re.match(SMSValidator.REGEX_PHONE, value) or re.match(SMSValidator.REGEX_PHONE_NO_HYPHEN, value)):
            raise serializers.ValidationError("전화번호 양식이 맞지않습니다.")
        return value.replace("-", "")

    @staticmethod
    def phone_unique(value: str) -> str:
        value = SMSValidator.phone_format(value)
        if User.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError("이미 사용 중인 전화번호입니다.")
        return value

    @staticmethod
    def code_digit(value: str) -> str:
        if not value.isdigit():
            raise serializers.ValidationError("인증 코드는 숫자만 입력 가능합니다.")
        return value


class SMSSendSerializer(serializers.Serializer[Any]):
    phone_number = serializers.CharField(required=True, max_length=20)

    def validate_phone_number(self, value: str) -> str:
        return SMSValidator.phone_unique(value)


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


class SMSVerifySerializer(serializers.Serializer[Any]):
    phone_number = serializers.CharField(required=True, max_length=20)
    code = serializers.CharField(required=True, min_length=6, max_length=6)

    def validate_phone_number(self, value: str) -> str:
        return SMSValidator.phone_format(value)

    def validate_code(self, value: str) -> str:
        return SMSValidator.code_digit(value)


class ChangePhoneSerializer(serializers.Serializer[Any]):
    phone_number = serializers.CharField(
        required=True, max_length=20, error_messages={"required": "휴대폰 번호를 입력해주세요."}
    )
    code = serializers.CharField(required=True, min_length=6, max_length=6)

    def validate_phone_number(self, value: str) -> str:
        return SMSValidator.phone_unique(value)

    def validate_code(self, value: str) -> str:
        return SMSValidator.code_digit(value)