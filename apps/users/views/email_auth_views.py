import secrets
from typing import Any

from django.core.cache import cache
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiExample, extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.models import User
from apps.users.serializers.email_auth_serializer import (
    EmailSerializer,
    EmailSignUpSerializer,
    EmailSignUpVerifySerializer,
    EmailVerifySerializer,
    FindEmailSerializer,
    PasswordResetSerializer,
)
from apps.users.utils.send_auth import SendAuth


class EmailSignUpView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(
        tags=["Account"],
        summary="회원 가입 시 이메일 인증 발송",
        description="회원 가입 시 필요한 인증용 이메일을 발송합니다.",
        request=EmailSignUpSerializer,
        methods=["POST"],
        responses={200: EmailSignUpSerializer, 400: OpenApiTypes.OBJECT},
        examples=[
            OpenApiExample(
                name="Success",
                response_only=True,
                status_codes=["200"],
                value={"detail": "회원가입을 위한 이메일 인증 코드가 전송되었습니다."},
            ),
            OpenApiExample(
                name="Bad Request",
                response_only=True,
                status_codes=["400"],
                value={"error_detail": {"code": ["이미 가입되어 있는 이메일 입니다."]}},
            ),
        ],
    )
    def post(self, request: Any, *args: Any, **kwargs: Any) -> Response:
        serializer = EmailSignUpSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"error_detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        email = serializer.validated_data["email"]

        email_auth = SendAuth.send_signup_email(email)

        if email_auth.status_code == status.HTTP_200_OK:
            return Response({"detail": "회원가입을 위한 이메일 인증 코드가 전송되었습니다."}, status=status.HTTP_200_OK)
        return email_auth


class EmailSignUpVerifyView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(
        tags=["Account"],
        summary="회원 가입 시 이메일 코드 검증",
        description="전송된 가입용 이메일 인증 코드를 검증합니다.",
        request=EmailSignUpVerifySerializer,
        methods=["POST"],
        responses={200: EmailSignUpVerifySerializer, 400: OpenApiTypes.OBJECT},
        examples=[
            OpenApiExample(
                name="Success",
                response_only=True,
                status_codes=["200"],
                value={"detail": "회원가입을 위한 이메일 인증에 성공하였습니다."},
            ),
            OpenApiExample(
                name="Bad Request",
                response_only=True,
                status_codes=["400"],
                value={"error_detail": {"email": ["인증 코드가 올바르지 않거나 만료되었습니다."]}},
            ),
        ],
    )
    def post(self, request: Any, *args: Any, **kwargs: Any) -> Response:
        serializer = EmailSignUpVerifySerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data["email"].lower()
            cache.set(f"verified:email:{email}", True, timeout=900)

            return Response({"detail": "회원가입을 위한 이메일 인증에 성공하였습니다."}, status=status.HTTP_200_OK)
        return Response({"error_detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class FindPasswordSendEmailView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(
        tags=["Account"],
        summary="비밀번호 재설정 시 이메일 인증 발송 API",
        description="비밀번호 재설정 시 이메일 인증 발송",
        request=inline_serializer(
            name="FindPasswordSendEmailVRequest",
            fields={
                "email": serializers.EmailField(required=True, help_text="user@example.com"),
            },
        ),
        examples=[
            OpenApiExample(
                name="Request",
                request_only=True,
                value={
                    "email": "user@example.com",
                },
            ),
            OpenApiExample(
                name="200 OK",
                response_only=True,
                status_codes=["200"],
                value={"detail": "비밀번호 찾기를 위한 이메일 인증 코드가 전송되었습니다."},
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
                name="FindPasswordSendEmailSuccess",
                fields={"detail": serializers.CharField()},
            ),
            400: inline_serializer(
                name="FindPasswordSendEmailError",
                fields={"error_detail": serializers.DictField()},
            ),
        },
    )
    def post(self, request: Any, *args: Any, **kwargs: Any) -> Response:
        serializer = EmailSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"error_detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        email = serializer.validated_data["email"]

        email_auth = SendAuth.send_password_reset_email(email)

        if email_auth.status_code == status.HTTP_200_OK:
            return Response(
                {"detail": "비밀번호 찾기를 위한 이메일 인증 코드가 전송되었습니다."}, status=status.HTTP_200_OK
            )
        return email_auth


class FindPasswordVerifyEmailView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(
        tags=["Account"],
        summary="비밀번호 재설정 시 이메일 인증 API",
        description="비밀번호 찾기 시 이메일 인증 코드를 검증하고 일회용 토큰을 발급합니다.",
        request=inline_serializer(
            name="FindPasswordVerifyEmailRequest",
            fields={
                "email": serializers.EmailField(required=True, help_text="user@example.com"),
                "code": serializers.CharField(required=True, min_length=6, max_length=6, help_text="123456"),
            },
        ),
        methods=["POST"],
        examples=[
            OpenApiExample(
                name="Request",
                request_only=True,
                value={"email": "user@example.com", "code": "a1ds21"},
            ),
            OpenApiExample(
                name="200 OK",
                response_only=True,
                status_codes=["200"],
                value={
                    "detail": "비밀번호 찾기를 위한 이메일 인증에 성공하였습니다.",
                    "reset_token": "dpiokwjfoiefjw21123131231231asdpijia",
                },
            ),
        ],
        responses={
            200: inline_serializer(
                name="FindPasswordVerifyEmailSuccess",
                fields={
                    "detail": serializers.CharField(),
                    "reset_token": serializers.CharField(),
                },
            ),
            400: inline_serializer(
                name="FindPasswordVerifyEmailError", fields={"error_detail": serializers.DictField()}
            ),
        },
    )
    def post(self, request: Any, *args: Any, **kwargs: Any) -> Response:
        serializer = EmailVerifySerializer(data=request.data)

        if not serializer.is_valid():
            return Response({"error_detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data["email"]
        code = serializer.validated_data["code"]

        redis_key = f"email:reset_password:{email}"
        stored_code = cache.get(redis_key)

        if not stored_code:
            return Response(
                {"error_detail": "인증 코드가 만료되었거나 존재하지 않습니다."}, status=status.HTTP_400_BAD_REQUEST
            )
        if not User.objects.filter(email=email).exists():
            cache.delete(redis_key)
            return Response({"error_detail": "등록된 이메일이 없습니다."}, status=status.HTTP_400_BAD_REQUEST)

        reset_token = secrets.token_hex(32)

        token_key = f"reset_token:{reset_token}"
        cache.set(token_key, email, timeout=300)
        if stored_code != code:
            return Response({"error_detail": "인증 코드가 올바르지 않습니다."}, status=status.HTTP_400_BAD_REQUEST)

        cache.delete(redis_key)
        cache.set(f"email_verified:reset_password:{email}", True, timeout=300)

        return Response(
            {"detail": "비밀번호 찾기를 위한 이메일 인증에 성공하였습니다.", "reset_token": reset_token},
            status=status.HTTP_200_OK,
        )
