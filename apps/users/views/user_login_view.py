from typing import Any

from drf_spectacular.utils import OpenApiExample, extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.serializers.login_serializer import LoginSerializer


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

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        response = Response({"access_token": access_token}, status=status.HTTP_200_OK)
        response.set_cookie(
            key="refresh_token",
            value=str(refresh),
            httponly=True,
            secure=True,  # 개발환경에서는 False, 배포시 True
            samesite="None",
            domain=".ozcoding.site",
            max_age=7 * 24 * 60 * 60,  # 7일
        )
        return response
