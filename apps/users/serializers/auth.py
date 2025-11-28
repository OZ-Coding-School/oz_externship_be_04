from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from apps.users.models import User as UserModel

User = get_user_model()


class UserSignUpSerializer(serializers.ModelSerializer[UserModel]):
    email = serializers.EmailField(
        required=True, validators=[UniqueValidator(queryset=User.objects.all(), message="이미 가입된 이메일 입니다.")]
    )
    nickname = serializers.CharField(
        required=True, validators=[UniqueValidator(queryset=User.objects.all(), message="이미 존재하는 닉네임 입니다.")]
    )
    phone_number = serializers.CharField(
        required=True, validators=[UniqueValidator(queryset=User.objects.all(), message="이미 가입된 전화번호 입니다.")]
    )
    password = serializers.CharField(style={"input_type": "password"}, write_only=True, required=True, min_length=8)

    class Meta:
        model = User
        fields = ("email", "password", "name", "nickname", "phone_number", "birthday", "gender")

    def validate_password(self, value: str) -> str:
        validate_password(value)
        return value
