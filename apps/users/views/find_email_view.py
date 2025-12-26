from typing import Any

from drf_spectacular.utils import (
    OpenApiExample,
    extend_schema,
    inline_serializer,
)
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.models.users import User
from apps.users.serializers.find_email_serializer import (
    FindEmailSMSSendSerializer,
    FindEmailVerifySerializer,
)
from apps.users.utils.send_sms import TwilioSendSms


class FindEmailView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Account"],
        summary="이메일 찾기 API",
        description="SMS 인증을 통해 사용자의 이메일을 찾습니다.",
        request=inline_serializer(
            name="FindEmailRequest",
            fields={
                "phone_number": serializers.CharField(required=True, help_text="01012345678"),
                "code": serializers.CharField(required=True, min_length=6, max_length=6, help_text="123456"),
            },
        ),
        examples=[
            OpenApiExample(
                name="Request",
                request_only=True,
                value={"phone_number": "01012345678", "code": "123456"},
            ),
            OpenApiExample(
                name="200 OK - Success",
                response_only=True,
                status_codes=["200"],
                value={"detail": "계정찾기 성공.", "email": "user@example.com"},
            ),
            OpenApiExample(
                name="400 Bad Request - Required Field",
                response_only=True,
                status_codes=["400"],
                value={"error_detail": {"phone_number": ["이 필드는 필수 항목입니다."]}},
            ),
            OpenApiExample(
                name="400 Bad Request - Invalid Code",
                response_only=True,
                status_codes=["400"],
                value={"error_detail": {"code": ["휴대폰 인증 실패 - 인증코드가 유효하지 않습니다."]}},
            ),
            OpenApiExample(
                name="400 Bad Request - Phone Not Found",
                response_only=True,
                status_codes=["400"],
                value={"error_detail": "등록된 전화번호가 없습니다."},
            ),
        ],
        responses={
            200: inline_serializer(
                name="FindEmailSuccess",
                fields={
                    "detail": serializers.CharField(),
                    "email": serializers.EmailField(),
                },
            ),
            400: inline_serializer(
                name="FindEmailError",
                fields={"error_detail": serializers.DictField()},
            ),
        },
    )
    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = FindEmailVerifySerializer(data=request.data)

        if not serializer.is_valid():
            return Response({"error_detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        phone_number = serializer.validated_data["phone_number"]
        code = serializer.validated_data["code"]

        verify_response = TwilioSendSms.verify_code(phone_number, code, "find_email")

        if verify_response.status_code != status.HTTP_200_OK:
            return Response(
                {"error_detail": {"code": ["휴대폰 인증 실패 - 인증코드가 유효하지 않습니다."]}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            user = User.objects.get(phone_number=phone_number)
        except User.DoesNotExist:
            return Response({"error_detail": "등록된 전화번호가 없습니다."}, status=status.HTTP_400_BAD_REQUEST)

        masked_email = self._mask_email(user.email)
        return Response({"detail": "계정찾기 성공.", "email": masked_email}, status=status.HTTP_200_OK)

    @staticmethod
    def _mask_email(email: str) -> str:
        try:
            local, domain = email.split("@")

            if len(local) <= 3:
                masked_local = local[0] + "***"
            else:
                masked_local = local[:3] + "***"

            return f"{masked_local}@{domain}"
        except (ValueError, IndexError):
            return "***@***.***"


class FindEmailSendSMSView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Account"],
        summary="이메일 찾기 SMS 인증 발송 API",
        description="이메일 찾기 시 이름과 전화번호로 본인 확인 후 SMS 인증 코드를 발송합니다.",
        request=inline_serializer(
            name="FindEmailSendSMSRequest",
            fields={
                "name": serializers.CharField(required=True, help_text="홍길동"),
                "phone_number": serializers.CharField(required=True, help_text="01012345678"),
            },
        ),
        examples=[
            OpenApiExample(
                name="Request",
                request_only=True,
                value={"name": "홍길동", "phone_number": "01012345678"},
            ),
            OpenApiExample(
                name="200 OK",
                response_only=True,
                status_codes=["200"],
                value={"detail": "계정찾기를 위한 휴대폰 인증 코드가 전송되었습니다."},
            ),
            OpenApiExample(
                name="400 Bad Request - Required",
                response_only=True,
                status_codes=["400"],
                value={
                    "error_detail": {
                        "name": ["이 필드는 필수 항목입니다."],
                        "phone_number": ["이 필드는 필수 항목입니다."],
                    }
                },
            ),
            OpenApiExample(
                name="400 Bad Request - Invalid",
                response_only=True,
                status_codes=["400"],
                value={"error_detail": {"phone_number": ["전화번호 양식이 맞지않습니다."]}},
            ),
            OpenApiExample(
                name="400 Bad Request - Not Found",
                response_only=True,
                status_codes=["400"],
                value={"error_detail": {"non_field_errors": ["등록된 정보가 없습니다."]}},
            ),
        ],
        responses={
            200: inline_serializer(
                name="FindEmailSendSMSSuccess",
                fields={"detail": serializers.CharField()},
            ),
            400: inline_serializer(
                name="FindEmailSendSMSError",
                fields={"error_detail": serializers.DictField()},
            ),
        },
    )
    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = FindEmailSMSSendSerializer(data=request.data)

        if not serializer.is_valid():
            return Response({"error_detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        phone_number = serializer.validated_data["phone_number"]
        return TwilioSendSms.send_find_email_sms(phone_number)
