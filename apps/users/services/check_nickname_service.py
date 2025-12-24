from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.exceptions import APIException

User = get_user_model()


class NicknameCheckConflict(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "중복된 닉네임이 존재합니다."
    default_code = "already_exist"


def nickname_check_service(nickname: str) -> None:
    if User.objects.filter(nickname=nickname).exists():
        raise NicknameCheckConflict()
