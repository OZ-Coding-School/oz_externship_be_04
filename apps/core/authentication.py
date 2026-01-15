from typing import Any

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import Token


class ActiveUserJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token: Token) -> Any:
        user = super().get_user(validated_token)
        if not user.is_active:
            raise AuthenticationFailed("탈퇴 처리된 계정입니다. 계정 복구를 진행해주세요.")
        return user
