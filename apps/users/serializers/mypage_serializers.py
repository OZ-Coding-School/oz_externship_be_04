from typing import Any

from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.core.constants import USER_PROFILE_IMAGE_UPLOAD_PATH
from apps.core.S3 import S3Uploader
from apps.users.services.mypage_services import NicknameCheckConflict

User = get_user_model()


class MyPageSerializer(serializers.ModelSerializer[Any]):
    profile_img_url = serializers.CharField(required=False, allow_null=True, allow_blank=True)
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

    def validate_profile_img_url(self, value: str) -> str:
        if not value:
            return value

        url = USER_PROFILE_IMAGE_UPLOAD_PATH
        if not value.startswith(url):
            raise serializers.ValidationError(f"잘못된 경로 입니다. {url}'로 시작해야 합니다.")
        return value

    def to_representation(self, instance: Any) -> dict[str, Any]:
        data = super().to_representation(instance)

        img_url = data.get("profile_img_url")
        if img_url:
            base_url = S3Uploader.get_s3_base_url()
            data["profile_img_url"] = f"{base_url}{img_url}"
        else:
            data["profile_img_url"] = None

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
