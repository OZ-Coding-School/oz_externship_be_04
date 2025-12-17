from typing import Any

from drf_spectacular.utils import OpenApiExample, extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken


class TokenRefreshView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(
        tags=["Account"],
        summary="토큰 재발급 API",
        description="쿠키의 refresh_token을 사용하여 새로운 access_token을 발급받습니다.",
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
            access_token = str(refresh.access_token)
            return Response({"access_token": access_token}, status=status.HTTP_200_OK)
        except TokenError:
            return Response(
                {"error_detail": "유효하지 않은 토큰입니다."},
                status=status.HTTP_401_UNAUTHORIZED,
            )


class LogoutView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(
        tags=["Account"],
        summary="로그아웃 API",
        description="로그아웃하여 refresh_token 쿠키를 삭제합니다.",
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
        response = Response({"detail": "로그아웃 되었습니다."}, status=status.HTTP_200_OK)
        response.delete_cookie("refresh_token")
        return response
