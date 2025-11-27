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
