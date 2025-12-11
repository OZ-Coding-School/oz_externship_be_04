from typing import Any, Dict

from rest_framework import serializers

from apps.users.models.users import User


class CompleteProfileSerializer(serializers.ModelSerializer[User]):
    class Meta:
        model = User
        fields = ["name", "phone_number", "gender", "birthday"]
        extra_kwargs = {
            "name": {"required": False},
            "phone_number": {"required": False},
            "gender": {"required": False},
            "birthday": {"required": False},
        }

    def validate_phone_number(self, value: str) -> str:
        if not value.isdigit() or len(value) not in (10, 11):
            raise serializers.ValidationError("전화번호를 입력해주세요.")
        return value
