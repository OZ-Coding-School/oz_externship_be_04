from typing import Any

from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class UserSerializer(serializers.ModelSerializer[Any]):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "password",
            "name",
            "nickname",
            "phone_number",
            "gender",
            "birthday",
            "profile_img_url",
            "is_active",
        )
        read_only_fields = ("id", "is_active")

    def validate_email(self, value: str) -> str:
        if self.instance is None:
            if User.objects.filter(email=value).exists():
                raise serializers.ValidationError("이미 사용 중인 이메일입니다.")
        return value

    def validate_nickname(self, value: str) -> str:
        if self.instance is None:
            if User.objects.filter(nickname=value).exists():
                raise serializers.ValidationError("이미 사용 중인 닉네임입니다.")
        return value

    def validate_phone_number(self, value: str) -> str:
        if self.instance is None:
            if User.objects.filter(phone_number=value).exists():
                raise serializers.ValidationError("이미 사용 중인 전화번호입니다.")
        return value

    def create(self, validated_data: dict[str, Any]) -> Any:
        password = validated_data.pop("password")
        user = User.objects.create_user(password=password, **validated_data)
        user.is_active = False
        user.save()
        return user

    def update(self, instance: Any, validated_data: dict[str, Any]) -> Any:
        password = validated_data.pop("password", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)

        instance.save()
        return instance
