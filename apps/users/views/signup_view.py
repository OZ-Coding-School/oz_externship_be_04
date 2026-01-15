from typing import Any

from django.core.cache import cache
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiExample, extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.serializers.signup_serializer import (
    EmailSignUpSerializer,
    EmailSignUpVerifySerializer,
    SignUpSerializer,
)
from apps.users.serializers.verification_serializer import (
    SMSSendSerializer,
    SMSVerifySerializer,
)
from apps.users.utils.send_auth import SendAuth
from apps.users.utils.send_sms import TwilioSendSms


class SignupView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(
        tags=["Account"],
        summary="회원가입 API",
        description="새로운 사용자 등록",
        request=inline_serializer(
            name="SignUpRequest",
            fields={
                "email": serializers.EmailField(required=True),
                "password": serializers.CharField(required=True),
                "nickname": serializers.CharField(required=True),
                "name": serializers.CharField(required=True),
                "phone_number": serializers.CharField(required=True, help_text="010-1234-5678,01012345678"),
                "birthday": serializers.DateField(required=True, help_text="YYYY-MM-DD"),
                "gender": serializers.ChoiceField(choices=["M", "F"], required=True),
            },
        ),
        examples=[
            OpenApiExample(
                name="SignUp",
                request_only=True,
                value={
                    "email": "example@example.com",
                    "password": "str",
                    "nickname": "str",
                    "name": "str",
                    "phone_number": "010-1234-5678",
                    "birthday": "1991-12-22",
                    "gender": "M",
                },
            ),
            OpenApiExample(
                name="201 Created",
                response_only=True,
                status_codes=["201"],
                value={"detail": "회원가입 완료"},
            ),
            OpenApiExample(
                name="400 Bad Request",
                response_only=True,
                status_codes=["400"],
                value={"error_detail": "이 필드는 필수 항목입니다."},
            ),
            OpenApiExample(
                name="409 Conflict",
                response_only=True,
                status_codes=["409"],
                value={"error_detail": "이미 중복된 회원가입 내역이 존재합니다."},
            ),
        ],
        responses={
            201: inline_serializer(
                name="SignUpSuccess",
                fields={"detail": serializers.CharField()},
            ),
            400: inline_serializer(
                name="SignUpValidationError",
                fields={"error_detail": serializers.CharField()},
            ),
            409: inline_serializer(name="SignUpConflictError", fields={"error_detail": serializers.CharField()}),
        },
    )
    def post(self, request: Request) -> Response:
        serializer = SignUpSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"detail": "회원가입 완료"}, status=status.HTTP_201_CREATED)

        first_error = str(list(serializer.errors.values())[0][0])

        if "이미 사용 중인" in first_error or "이미 존재합니다" in first_error:
            return Response(
                {"error_detail": "이미 중복된 회원가입 내역이 존재합니다."},
                status=status.HTTP_409_CONFLICT,
            )

        return Response({"error_detail": first_error}, status=status.HTTP_400_BAD_REQUEST)


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
