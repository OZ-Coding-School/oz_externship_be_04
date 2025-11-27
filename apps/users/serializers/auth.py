from typing import Any

from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.users.models import User as UserModel

User = get_user_model()


class UserSignUpSerializer(serializers.ModelSerializer[UserModel]):
    email = serializers.EmailField()
    password = serializers.CharField(style={"input_type": "password"}, write_only=True)

    class Meta:
        model = User
        fields = ("email", "password", "name", "nickname", "phone_number", "birthday", "gender")

    def create(self, validated_data: Any) -> UserModel:
        user = User.objects.create_user(  # type: ignore
            email=validated_data["email"],
            password=validated_data["password"],
            name=validated_data["name"],
            nickname=validated_data["nickname"],
            phone_number=validated_data["phone_number"],
            birthday=validated_data["birthday"],
            gender=validated_data["gender"],
        )
        return user  # type: ignore
