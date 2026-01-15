from typing import TYPE_CHECKING, Any, cast

from drf_spectacular.utils import OpenApiExample, extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.models import User
from apps.users.serializers.change_phone_serializer import ChangePhoneSerializer
from apps.users.serializers.verification_serializer import SMSSendSerializer
from apps.users.utils.send_sms import TwilioSendSms

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser


class ChangePhoneSendSMSView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Account"],
        summary="회원 정보 수정 시 휴대폰 번호 SMS 인증 발송 API",
        description="회원 정보 수정 시 휴대폰 번호 변경을 위한 SMS 인증 코드를 발송합니다.",
        request=inline_serializer(
            name="ChangePhoneSendSMSRequest",
            fields={
                "phone_number": serializers.CharField(required=True, help_text="01012345678"),
            },
        ),
        examples=[
            OpenApiExample(
                name="Request",
                request_only=True,
                value={"phone_number": "01012345678"},
            ),
            OpenApiExample(
                name="200 OK",
                response_only=True,
                status_codes=["200"],
                value={"detail": "휴대폰 번호 변경을 위한 휴대폰 인증 코드가 전송되었습니다."},
            ),
            OpenApiExample(
                name="400 Bad Request - Required",
                response_only=True,
                status_codes=["400"],
                value={"error_detail": {"phone_number": ["이 필드는 필수 항목입니다."]}},
            ),
            OpenApiExample(
                name="400 Bad Request - Invalid",
                response_only=True,
                status_codes=["400"],
                value={"error_detail": {"phone_number": ["전화번호 양식이 맞지않습니다."]}},
            ),
            OpenApiExample(
                name="400 Bad Request - Duplicate",
                response_only=True,
                status_codes=["400"],
                value={"error_detail": {"phone_number": ["이미 사용 중인 전화번호입니다."]}},
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
                name="ChangePhoneSendSMSSuccess",
                fields={"detail": serializers.CharField()},
            ),
            400: inline_serializer(
                name="ChangePhoneSendSMSError",
                fields={"error_detail": serializers.DictField()},
            ),
            401: inline_serializer(
                name="ChangePhoneSendSMSUnauthorized",
                fields={"error_detail": serializers.CharField()},
            ),
        },
    )
    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = SMSSendSerializer(data=request.data)

        if not serializer.is_valid():
            return Response({"error_detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        phone_number = serializer.validated_data["phone_number"]

        user = cast("User", request.user)

        if phone_number == user.phone_number:
            return TwilioSendSms.send_change_phone_sms(phone_number)

        return TwilioSendSms.send_change_phone_sms(phone_number)


class ChangePhoneView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Account"],
        summary="회원 정보 수정 시 휴대폰 번호 SMS 인증 API",
        description="SMS 인증 코드를 검증하고 휴대폰 번호를 변경합니다.",
        request=inline_serializer(
            name="ChangePhoneRequest",
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
                name="200 OK",
                response_only=True,
                status_codes=["200"],
                value={"detail": "휴대폰 번호가 변경되었습니다."},
            ),
            OpenApiExample(
                name="400 Bad Request - Required",
                response_only=True,
                status_codes=["400"],
                value={
                    "error_detail": {
                        "phone_number": ["이 필드는 필수 항목입니다."],
                        "code": ["이 필드는 필수 항목입니다."],
                    }
                },
            ),
            OpenApiExample(
                name="400 Bad Request - Invalid Code",
                response_only=True,
                status_codes=["400"],
                value={"error_detail": "인증 실패: 코드가 일치하지 않거나 만료되었습니다."},
            ),
            OpenApiExample(
                name="400 Bad Request - Duplicate",
                response_only=True,
                status_codes=["400"],
                value={"error_detail": {"phone_number": ["이미 사용 중인 전화번호입니다."]}},
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
                name="ChangePhoneSuccess",
                fields={"detail": serializers.CharField()},
            ),
            400: inline_serializer(
                name="ChangePhoneError",
                fields={"error_detail": serializers.DictField()},
            ),
            401: inline_serializer(
                name="ChangePhoneUnauthorized",
                fields={"error_detail": serializers.CharField()},
            ),
        },
    )
    def patch(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = ChangePhoneSerializer(data=request.data)

        if not serializer.is_valid():
            return Response({"error_detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        phone_number = serializer.validated_data["phone_number"]
        code = serializer.validated_data["code"]

        verify_response = TwilioSendSms.verify_code(phone_number, code, "change_phone")

        if verify_response.status_code != 200:
            return verify_response

        user = cast(User, request.user)
        user.phone_number = phone_number
        user.save()

        TwilioSendSms.clear_verification(phone_number, "change_phone")

        return Response({"detail": "휴대폰 번호가 변경되었습니다."}, status=status.HTTP_200_OK)
