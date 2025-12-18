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


class EmailVerifySerializer(serializers.Serializer[Any]):
    email = serializers.EmailField(required=True)
    code = serializers.CharField(
        required=True, min_length=6, max_length=6, error_messages={"required": "인증 코드를 입력해주세요."}
    )

    def validate_code(self, value: str) -> str:
        if not value.isdigit():
            raise serializers.ValidationError("인증 코드는 숫자만 입력 가능합니다.")
        return value


class FindEmailSerializer(serializers.Serializer[Any]):
    name = serializers.CharField(required=True, max_length=20, error_messages={"required": "이름을 입력해주세요."})

    phone_number = serializers.CharField(
        required=True, max_length=20, error_messages={"required": "휴대폰 번호를 입력해주세요."}
    )

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        name = attrs.get("name")
        phone_number = attrs.get("phone_number")

        if phone_number is None:
            raise serializers.ValidationError({"phone_number": ["휴대폰 번호가 제공되지 않았습니다."]})

        phone_number = phone_number.replace("-", "")
        attrs["phone_number"] = phone_number

        user = User.objects.filter(name=name, phone_number=phone_number).first()

        if not user:
            raise serializers.ValidationError("등록된 정보가 없습니다.")

        attrs["user"] = user

        return attrs
