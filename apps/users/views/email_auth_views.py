from typing import Any

from django.core.cache import cache
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.serializers.email_auth_serializer import (
    EmailSignUpSerializer,
    EmailSignUpVerifySerializer,
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
