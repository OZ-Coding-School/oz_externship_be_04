from typing import Any, Dict

from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError

User = get_user_model()


def account_update_service(user: Any, validated_data: Dict[str, Any]) -> Any:
    user.profile_img_url = validated_data.get("profile_img_url", user.profile_img_url)
    user.name = validated_data.get("name", user.name)
    user.nickname = validated_data.get("nickname", user.nickname)
    user.birthday = validated_data.get("birthday", user.birthday)
    user.gender = validated_data.get("gender", user.gender)

    user.save()
    return user


def password_reset_service(user: Any, validated_data: Dict[str, Any]) -> Any:
    current_password = validated_data.get("current_password")
    new_password = validated_data.get("new_password")

    if not user.check_password(current_password):
        raise ValidationError({"current_password": ["현재 비밀번호가 일치하지 않습니다."]})

    user.set_password(new_password)
    user.save()
    return user
