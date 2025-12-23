import secrets
from typing import Any

from django.core.cache import cache
from drf_spectacular.utils import OpenApiExample, extend_schema, inline_serializer
from rest_framework import permissions, serializers, status
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.models.users import User
from apps.users.serializers.email_auth_serializer import PasswordResetSerializer
from apps.users.serializers.mypage_serializers import PasswordChangeSerializer
from apps.users.services.mypage_services import password_reset_service


class FindPasswordView(APIView):
    permission_classes = []

    def get_permissions(self) -> list[BasePermission]:
        if self.request.method == "POST":
            return [permissions.AllowAny()]
        elif self.request.method == "PATCH":
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    @extend_schema(
        tags=["Account"],
        summary="비밀번호 재설정 API (토큰 기반)",
        description="이메일 인증 후 발급받은 토큰으로 새 비밀번호로 변경합니다.",
        request=inline_serializer(
            name="PasswordResetRequest",
            fields={
                "token": serializers.CharField(
                    required=True, max_length=64, help_text="a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6"
                ),
                "new_password": serializers.CharField(required=True, min_length=8, help_text="Pass1234!@"),
            },
        ),
        examples=[
            OpenApiExample(
                name="Request",
                request_only=True,
                value={"token": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6", "new_password": "NewPass1234!@"},
            ),
            OpenApiExample(
                name="200 OK - Success",
                response_only=True,
                status_codes=["200"],
                value={"detail": "비밀번호 변경 성공."},
            ),
            OpenApiExample(
                name="400 Bad Request - Invalid Token",
                response_only=True,
                status_codes=["400"],
                value={"error_detail": "유효하지 않거나 만료된 토큰입니다."},
            ),
            OpenApiExample(
                name="400 Bad Request - Required Field",
                response_only=True,
                status_codes=["400"],
                value={"error_detail": {"new_password": ["이 필드는 필수 항목입니다."]}},
            ),
            OpenApiExample(
                name="400 Bad Request - Weak Password",
                response_only=True,
                status_codes=["400"],
                value={"error_detail": {"new_password": ["이 비밀번호는 너무 일반적입니다."]}},
            ),
            OpenApiExample(
                name="400 Bad Request - Short Password",
                response_only=True,
                status_codes=["400"],
                value={
                    "error_detail": {"new_password": ["이 비밀번호는 너무 짧습니다. 최소 8 문자를 포함해야 합니다."]}
                },
            ),
            OpenApiExample(
                name="400 Bad Request - Numeric Only",
                response_only=True,
                status_codes=["400"],
                value={"error_detail": {"new_password": ["이 비밀번호는 숫자로만 되어 있습니다."]}},
            ),
        ],
        responses={
            200: inline_serializer(
                name="PasswordResetSuccess",
                fields={"detail": serializers.CharField()},
            ),
            400: inline_serializer(
                name="PasswordResetError",
                fields={"error_detail": serializers.DictField()},
            ),
        },
    )
    def post(self, request: Any) -> Response:
        serializer = PasswordResetSerializer(data=request.data)

        if not serializer.is_valid():
            return Response({"error_detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        token = serializer.validated_data["token"]
        new_password = serializer.validated_data["new_password"]

        cache_key = f"reset_token:{token}"
        email = cache.get(cache_key)

        if not email:
            return Response({"error_detail": "유효하지 않거나 만료된 토큰입니다."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            cache.delete(cache_key)
            return Response({"error_detail": "등록된 이메일이 없습니다."}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()

        cache.delete(cache_key)

        return Response({"detail": "비밀번호 변경 성공."}, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["Account"],
        summary="마이페이지 비밀번호 재설정 API",
        description="현재 로그인 된 유저의 비밀번호를 변경합니다.",
        request=inline_serializer(
            name="MyPagePasswordChangeRequest",
            fields={
                "current_password": serializers.CharField(required=True, help_text="OldPass1234!"),
                "new_password": serializers.CharField(required=True, min_length=8, help_text="NewPass1234!@"),
                "confirm_password": serializers.CharField(required=True, help_text="NewPass1234!@"),
            },
        ),
        examples=[
            OpenApiExample(
                name="Request",
                request_only=True,
                value={
                    "current_password": "OldPass1234!",
                    "new_password": "NewPass1234!@",
                    "confirm_password": "NewPass1234!@",
                },
            ),
            OpenApiExample(
                name="200 OK - Success",
                response_only=True,
                status_codes=["200"],
                value={"detail": "비밀번호 변경 성공."},
            ),
            OpenApiExample(
                name="400 Bad Request - Current Password Mismatch",
                response_only=True,
                status_codes=["400"],
                value={"error_detail": {"current_password": ["현재 비밀번호가 일치하지 않습니다."]}},
            ),
            OpenApiExample(
                name="400 Bad Request - New Password Mismatch",
                response_only=True,
                status_codes=["400"],
                value={"error_detail": {"new_password": ["새 비밀번호가 일치하지 않습니다."]}},
            ),
            OpenApiExample(
                name="400 Bad Request - Weak Password",
                response_only=True,
                status_codes=["400"],
                value={"error_detail": {"new_password": ["이 비밀번호는 너무 일반적입니다."]}},
            ),
            OpenApiExample(
                name="401 Unauthorized",
                response_only=True,
                status_codes=["401"],
                value={"error_detail": "자격 인증 데이터가 제공되지 않았습니다."},
            ),
        ],
        responses={
            200: inline_serializer(
                name="MyPagePasswordChangeSuccess",
                fields={"detail": serializers.CharField()},
            ),
            400: inline_serializer(
                name="MyPagePasswordChangeError",
                fields={"error_detail": serializers.DictField()},
            ),
            401: inline_serializer(
                name="UnauthorizedError_PW",
                fields={"error_detail": serializers.CharField()},
            ),
        },
    )
    def patch(self, request: Any) -> Response:
        serializer = PasswordChangeSerializer(data=request.data, context={"request": request})

        if serializer.is_valid():
            password_reset_service(request.user, serializer.validated_data)
            return Response({"detail": "비밀번호 변경 성공."}, status=status.HTTP_200_OK)

        return Response({"error_detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
