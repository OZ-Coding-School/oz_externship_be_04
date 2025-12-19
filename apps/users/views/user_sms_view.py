from typing import TYPE_CHECKING, Any, cast

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiResponse,
    extend_schema,
    inline_serializer,
)
from rest_framework import permissions, serializers, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.models.users import User
from apps.users.serializers.sms_serializer import (
    ChangePhoneSerializer,
    FindEmailSMSSendSerializer,
    SMSSendSerializer,
    SMSVerifySerializer,
)
from apps.users.utils.send_sms import TwilioSendSms

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser


class SignupSendSMSView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Account"],
        summary="회원가입 SMS 인증 발송 API",
        description="회원가입 시 SMS 인증 코드를 발송합니다.",
        request=inline_serializer(
            name="SignupSendSMSRequest",
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
                value={"detail": "회원가입을 위한 휴대폰 인증 코드가 전송되었습니다."},
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
        ],
        responses={
            200: inline_serializer(
                name="SignupSendSMSSuccess",
                fields={"detail": serializers.CharField()},
            ),
            400: inline_serializer(
                name="SignupSendSMSError",
                fields={"error_detail": serializers.DictField()},
            ),
        },
    )
    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = SMSSendSerializer(data=request.data)

        if not serializer.is_valid():
            return Response({"error_detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        phone_number = serializer.validated_data["phone_number"]
        return TwilioSendSms.send_signup_sms(phone_number)


class SignupVerifySMSView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Account"],
        summary="회원가입 SMS 인증 검증 API",
        description="회원가입 시 SMS 인증 코드를 검증합니다.",
        request=inline_serializer(
            name="SignupVerifySMSRequest",
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
                value={"detail": "회원가입을 위한 휴대폰 인증에 성공하였습니다."},
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
                name="400 Bad Request - Invalid",
                response_only=True,
                status_codes=["400"],
                value={"error_detail": "인증 실패: 코드가 일치하지 않거나 만료되었습니다."},
            ),
        ],
        responses={
            200: inline_serializer(
                name="SignupVerifySMSSuccess",
                fields={"detail": serializers.CharField()},
            ),
            400: inline_serializer(
                name="SignupVerifySMSError",
                fields={"error_detail": serializers.DictField()},
            ),
        },
    )
    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = SMSVerifySerializer(data=request.data)

        if not serializer.is_valid():
            return Response({"error_detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        phone_number = serializer.validated_data["phone_number"]
        code = serializer.validated_data["code"]

        return TwilioSendSms.verify_code(phone_number, code, "signup")


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
