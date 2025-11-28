from typing import Any, Dict

from django.db import IntegrityError, transaction
from rest_framework.exceptions import ValidationError

from apps.users.models import User


class AuthService:
    def signup(self, validated_data: Dict[str, Any]) -> User:
        email = validated_data.pop("email")
        password = validated_data.pop("password")

        try:
            with transaction.atomic():
                user = User.objects.create_user(email=email, password=password, **validated_data)
                return user

        except IntegrityError:
            raise ValidationError("데이터 처리중 오류가 발생했습니다.")
        except Exception as e:
            raise ValidationError(f"회원가입 도중 오류가 발생했습니다. (Error: {str(e)})")
