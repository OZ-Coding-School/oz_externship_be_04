from typing import Any

from django.conf import settings
from django.core.cache import cache
from drf_spectacular.utils import OpenApiExample, extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.serializers.login_serializer import LoginSerializer
from apps.users.models import User

check_secure = not settings.DEBUG
check_samesite = "None" if not settings.DEBUG else "Lax"
check_domain = ".ozcoding.site" if not settings.DEBUG else None


def blacklist_token(token: RefreshToken) -> None:
    jti = token.payload.get("jti")
    exp = token.payload.get("exp")
    if jti and exp:
        import time

        ttl = exp - int(time.time())
        if ttl > 0:
            cache.set(f"blacklist:{jti}", "1", timeout=ttl)


def is_token_blacklisted(token: RefreshToken) -> bool:
    jti = token.payload.get("jti")
    return cache.get(f"blacklist:{jti}") is not None


class LoginView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(
        tags=["Account"],
        summary="로그인 API",
        description="로그인하여 access 토큰을 발급받습니다.",
        request=inline_serializer(
            name="LoginRequest",
            fields={
                "email": serializers.EmailField(required=True, help_text="example@example.com"),
                "password": serializers.CharField(required=True),
            },
        ),
        examples=[
            OpenApiExample(
                name="Login",
                request_only=True,
                value={
                    "email": "user@example.com",
                    "password": "Password1234@@",
                },
            ),
            OpenApiExample(
                name="200 OK",
                response_only=True,
                status_codes=["200"],
                value={"access_token": "JWT token value"},
            ),
            OpenApiExample(
                name="400 Bad Request",
                response_only=True,
                status_codes=["400"],
                value={"error_detail": {"password": "이 필드는 필수 항목입니다."}},
            ),
            OpenApiExample(
                name="403 Forbidden",
                response_only=True,
                status_codes=["403"],
                value={"error_detail": "탈퇴 처리된 계정입니다. 계정 복구를 진행해주세요."},
            ),
        ],
        responses={
            200: inline_serializer(
                name="LoginSuccess",
                fields={"access_token": serializers.CharField()},
            ),
            400: inline_serializer(
                name="LoginError",
                fields={"error_detail": serializers.DictField()},
            ),
            403: inline_serializer(
                name="LoginForbidden",
                fields={"error_detail": serializers.CharField()},
            ),
        },
    )
    def post(self, request: Request, *args: list[Any], **kwargs: dict[str, Any]) -> Response:
        serializer = LoginSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {"error_detail": "이메일 또는 비밀번호가 일치하지 않습니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user = serializer.validated_data["user"]

        if not user.is_active:
            return Response(
                {"error_detail": "탈퇴 처리된 계정입니다. 계정 복구를 진행해주세요"},
                status=status.HTTP_403_FORBIDDEN,
            )

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        response = Response({"access_token": access_token}, status=status.HTTP_200_OK)
        response.set_cookie(
            key="refresh_token",
            value=str(refresh),
            httponly=True,
            secure=check_secure,
            samesite="None" if not settings.DEBUG else "Lax",
            domain=check_domain,
            max_age=7 * 24 * 60 * 60,
        )
        return response


class TokenRefreshView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(
        tags=["Account"],
        summary="토큰 재발급 API",
        description="쿠키의 refresh_token을 사용하여 새로운 access_token을 발급받습니다. 기존 refresh_token은 블랙리스트 처리되고 새로운 refresh_token이 발급됩니다.",
        responses={
            200: inline_serializer(
                name="TokenRefreshSuccess",
                fields={"access_token": serializers.CharField()},
            ),
            401: inline_serializer(
                name="TokenRefreshError",
                fields={"error_detail": serializers.CharField()},
            ),
        },
        examples=[
            OpenApiExample(
                name="200 OK",
                response_only=True,
                status_codes=["200"],
                value={"access_token": "JWT token value"},
            ),
            OpenApiExample(
                name="401 Unauthorized",
                response_only=True,
                status_codes=["401"],
                value={"error_detail": "유효하지 않은 토큰입니다."},
            ),
        ],
    )
    def post(self, request: Request, *args: list[Any], **kwargs: dict[str, Any]) -> Response:
        refresh_token = request.COOKIES.get("refresh_token")

        if not refresh_token:
            return Response(
                {"error_detail": "리프레시 토큰이 없습니다."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            refresh = RefreshToken(refresh_token)  # type: ignore[arg-type]

            if is_token_blacklisted(refresh):
                return Response(
                    {"error_detail": "유효하지 않은 토큰입니다."},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            blacklist_token(refresh)

            user = User.objects.get(id=refresh.payload.get("user_id"))
            new_refresh = RefreshToken.for_user(user)
            access_token = str(new_refresh.access_token)

            response = Response({"access_token": access_token}, status=status.HTTP_200_OK)
            response.set_cookie(
                key="refresh_token",
                value=str(new_refresh),
                httponly=True,
                secure=check_secure,
                samesite=check_samesite,  # type: ignore
                domain=check_domain,
                max_age=7 * 24 * 60 * 60,
            )
            return response
        except (TokenError, User.DoesNotExist):
            return Response(
                {"error_detail": "유효하지 않은 토큰입니다."},
                status=status.HTTP_401_UNAUTHORIZED,
            )


class LogoutView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(
        tags=["Account"],
        summary="로그아웃 API",
        description="로그아웃하여 refresh_token을 블랙리스트에 추가하고 쿠키를 삭제합니다.",
        responses={
            200: inline_serializer(
                name="LogoutSuccess",
                fields={"detail": serializers.CharField()},
            ),
        },
        examples=[
            OpenApiExample(
                name="200 OK",
                response_only=True,
                status_codes=["200"],
                value={"detail": "로그아웃 되었습니다."},
            ),
        ],
    )
    def post(self, request: Request, *args: list[Any], **kwargs: dict[str, Any]) -> Response:
        refresh_token = request.COOKIES.get("refresh_token")

        if refresh_token:
            try:
                refresh = RefreshToken(refresh_token)  # type: ignore[arg-type]
                blacklist_token(refresh)
            except TokenError:
                pass

        response = Response({"detail": "로그아웃 되었습니다."}, status=status.HTTP_200_OK)
        response.delete_cookie("refresh_token")
        return response
