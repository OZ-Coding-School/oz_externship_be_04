from typing import Any

from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.serializers.restore_serializers import (
    RestoreEmailCodeSerializer,
    RestoreWithdrawalSerializer,
)
from apps.users.utils.send_auth import SendAuth


class RestoreSendEmailView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(
        tags=["Account"],
        summary="계정 복구 인증 이메일 발송",
        description="입력한 이메일로 인증 코드를 발송합니다.",
        request=RestoreWithdrawalSerializer,
        methods=["POST"],
        responses={
            200: OpenApiResponse(
                description="발송 성공",
                examples=[
                    OpenApiExample("발송 성공", value={"detail": "계정복구를 위한 이메일 인증 코드가 전송되었습니다."})
                ],
            ),
            400: OpenApiResponse(
                description="발송 실패",
                examples=[
                    OpenApiExample("발송 실패", value={"error_detail": {"email": ["가입된 이메일이 아닙니다."]}})
                ],
            ),
        },
    )
    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = RestoreWithdrawalSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"error_detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        email = serializer.validated_data["email"]
        auth_response = SendAuth.send_restore_email(email)

        if auth_response.status_code == 200:
            return Response({"detail": "계정복구를 위한 이메일 인증 코드가 전송되었습니다."}, status=status.HTTP_200_OK)
        return auth_response


class RestoreAccountView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(
        tags=["Account"],
        summary="계정 복구 처리",
        description="인증 코드를 확인하여 해당 계정을 복구합니다.",
        request=RestoreEmailCodeSerializer,
        methods=["POST"],
        responses={
            200: OpenApiResponse(
                description="복구 성공",
                examples=[OpenApiExample("성공 예시", value={"detail": "계정복구가 완료되었습니다."})],
            ),
            400: OpenApiResponse(
                description="복구 실패",
                examples=[
                    OpenApiExample(
                        "복구 실패",
                        value={"error_detail": {"code": ["이메일 인증 실패 - 이메일 인증코드가 유효하지 않습니다."]}},
                    )
                ],
            ),
        },
    )
    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = RestoreEmailCodeSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response({"detail": "계정복구가 완료되었습니다."}, status=status.HTTP_200_OK)

        errors = serializer.errors
        if "error_detail" in errors:
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"error_detail": errors}, status=status.HTTP_400_BAD_REQUEST)
