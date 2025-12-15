from typing import Any

from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.users.services.mypage_services import NicknameCheckConflict

User = get_user_model()


class MyPageSerializer(serializers.ModelSerializer[Any]):
    role = serializers.CharField(read_only=True)
    birthday = serializers.DateField(input_formats=["%Y%m%d", "%Y-%m-%d"])

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "nickname",
            "name",
            "phone_number",
            "birthday",
            "gender",
            "profile_img_url",
            "created_at",
            "updated_at",
            "role",
        ]
        read_only_fields = ["id", "email", "phone_number", "created_at", "updated_at", "role"]
        extra_kwargs: Any = {"nickname": {"validators": []}}

    def validate_nickname(self, value: str) -> str:
        if self.instance.nickname == value:  # type: ignore
            return value

        if User.objects.filter(nickname=value).exists():
            raise NicknameCheckConflict()
        return value

    def to_representation(self, instance: Any) -> dict[str, Any]:
        data = super().to_representation(instance)

        if not data.get("profile_img_url"):
            data["profile_img_url"] = "https://example.com/profile/user1.png"

        request = self.context.get("request")
        if request.method == "GET":  # type: ignore
            data.pop("updated_at", None)
        elif request.method == "PATCH":  # type: ignore
            data.pop("phone_number", None)
            data.pop("created_at", None)

        return data


class PasswordResetSerializer(serializers.Serializer[Any]):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, data: Any) -> Any:
        new_password = data["new_password"]
        confirm_password = data["confirm_password"]

        if new_password != confirm_password:
            raise serializers.ValidationError({"new_password": ["새 비밀번호가 일치하지 않습니다."]})
        return data
