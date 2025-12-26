import secrets
from typing import Any

from django.conf import settings
from django.core.cache import cache
from drf_spectacular.utils import OpenApiExample, extend_schema, inline_serializer
from rest_framework import permissions, serializers, status
from rest_framework.permissions import AllowAny, BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.models.users import User
from apps.users.serializers.find_password_serializer import (
    PasswordChangeSerializer,
    PasswordResetSerializer,
)
from apps.users.serializers.verification_serializer import (
    EmailSerializer,
    EmailVerifySerializer,
)
from apps.users.services.mypage_services import password_reset_service
from apps.users.utils.send_auth import SendAuth

check_secure = not settings.DEBUG
check_samesite = "None" if not settings.DEBUG else "Lax"
check_domain = ".ozcoding.site" if not settings.DEBUG else None


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
        summary="비밀번호 재설정 API (쿠키 자동 인증)",
        description="쿠키 기반 비밀번호 재설정",
        request=inline_serializer(
            name="PasswordResetRequestCookie",
            fields={
                "new_password": serializers.CharField(
                    required=True, min_length=8, help_text="새 비밀번호 (최소 8자, 숫자만으로 구성 불가)"
                ),
            },
        ),
        examples=[
            OpenApiExample(
                name="Request (쿠키 자동 전송)",
                request_only=True,
                value={"new_password": "NewPass1234!@"},
                description="쿠키의 password_reset_token이 자동으로 전송됩니다.",
            ),
            OpenApiExample(
                name="200 OK - Success",
                response_only=True,
                status_codes=["200"],
                value={"detail": "비밀번호 변경 성공."},
            ),
            OpenApiExample(
                name="400 Bad Request - No Cookie",
                response_only=True,
                status_codes=["400"],
                value={"error_detail": "인증 토큰이 없습니다. 이메일 인증을 먼저 완료해주세요."},
                description="쿠키에 password_reset_token이 없는 경우",
            ),
            OpenApiExample(
                name="400 Bad Request - Invalid Token",
                response_only=True,
                status_codes=["400"],
                value={"error_detail": "유효하지 않거나 만료된 토큰입니다."},
                description="토큰이 만료되었거나 잘못된 경우",
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
            OpenApiExample(
                name="400 Bad Request - User Not Found",
                response_only=True,
                status_codes=["400"],
                value={"error_detail": "등록된 이메일이 없습니다."},
                description="토큰에 해당하는 사용자가 없는 경우",
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
        token = request.COOKIES.get("password_reset_token")

        if not token:
            return Response(
                {"error_detail": "인증 토큰이 없습니다. 이메일 인증을 먼저 완료해주세요."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = request.data.copy()
        data["token"] = token

        serializer = PasswordResetSerializer(data=data)

        if not serializer.is_valid():
            return Response({"error_detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        new_password = serializer.validated_data["new_password"]

        cache_key = f"reset_token:{token}"
        email = cache.get(cache_key)

        if not email:
            response = Response(
                {"error_detail": "유효하지 않거나 만료된 토큰입니다."}, status=status.HTTP_400_BAD_REQUEST
            )
            response.delete_cookie("password_reset_token")
            return response

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            cache.delete(cache_key)
            response = Response({"error_detail": "등록된 이메일이 없습니다."}, status=status.HTTP_400_BAD_REQUEST)
            response.delete_cookie("password_reset_token")
            return response

        user.set_password(new_password)
        user.save()

        cache.delete(cache_key)

        response = Response({"detail": "비밀번호 변경 성공."}, status=status.HTTP_200_OK)

        response.delete_cookie(key="password_reset_token", path="/api/v1/accounts/find-password")

        return response

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
        description="비밀번호 찾기 시 이메일 인증 코드를 검증하고 일회용 토큰을 쿠키에저장합니다.",
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
                    "expires_in": 300,
                },
            ),
        ],
        responses={
            200: inline_serializer(
                name="FindPasswordVerifyEmailSuccess",
                fields={
                    "detail": serializers.CharField(),
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

        if stored_code != code:
            return Response({"error_detail": "인증 코드가 올바르지 않습니다."}, status=status.HTTP_400_BAD_REQUEST)

        if not User.objects.filter(email=email).exists():
            cache.delete(redis_key)
            return Response({"error_detail": "등록된 이메일이 없습니다."}, status=status.HTTP_400_BAD_REQUEST)

        reset_token = secrets.token_hex(32)

        token_key = f"reset_token:{reset_token}"
        token_ttl = 300
        cache.set(token_key, email, timeout=token_ttl)

        cache.delete(redis_key)

        response = Response(
            {"detail": "비밀번호 찾기를 위한 이메일 인증에 성공하였습니다.", "expires_in": token_ttl},
            status=status.HTTP_200_OK,
        )

        response.set_cookie(
            key="password_reset_token",
            value=reset_token,
            max_age=token_ttl,
            httponly=True,
            secure=check_secure,
            samesite="None" if not settings.DEBUG else "Lax",
            domain=check_domain,
            path="accounts/find-password",
        )

        return response
