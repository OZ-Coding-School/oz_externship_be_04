from typing import Any, Dict

from apps.users.models import User


class AuthService:
    def signup(self, validated_data: Dict[str, Any]) -> User:
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
