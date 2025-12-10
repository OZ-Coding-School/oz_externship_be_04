from typing import Any

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiExample, extend_schema, extend_schema_view
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.serializers.withdrawal_serializers import WithdrawalSerializer
from apps.users.services.withdrawal_services import withdraw_service


@extend_schema_view(
    delete=extend_schema(
        tags=["Account"],
        summary="회원 탈퇴",
        description="회원 탈퇴를 위한 스키마 입니다. 14일 후 영구 삭제 됩니다.",
        request=WithdrawalSerializer,
        methods=["DELETE"],
        responses={200: OpenApiTypes.OBJECT, 400: OpenApiTypes.OBJECT},
        examples=[
            OpenApiExample(
                request_only=True,
                name="success_case",
                summary="탈퇴 요청 데이터 예시",
                value={
                    "reason": "TOO_DIFFICULT",
                    "reason_detail": "탈퇴 테스트 양식 입니다.",
                    "agree_check": True,
                },
            ),
            OpenApiExample(
                response_only=True,
                name="success_response",
                summary="탈퇴 성공 응답 예시",
                value={
                    "detail": "회원 탈퇴 처리가 완료되었습니다. 14일 후 계정이 영구 삭제되며, 그전에 다시 로그인하시면 계정을 복구하실 수 있습니다."
                },
                status_codes=["200"],
            ),
            OpenApiExample(
                response_only=True,
                name="error_response",
                summary="탈퇴 실패 예시 (이미 탈퇴함)",
                value={
                    "error_detail": {
                        "non_field_errors": [
                            "이미 탈퇴 처리된 유저 입니다. 다시 로그인 하시면 계정 복구를 진행하실 수 있습니다."
                        ]
                    }
                },
                status_codes=["400"],
            ),
        ],
    )
)
class UserAccountView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def delete(self, request: Any, *args: Any, **kwargs: Any) -> Response:
        serializer = WithdrawalSerializer(data=request.data)

        if not serializer.is_valid():
            return Response({"error_detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        data.pop("agree_check")

        withdraw_service(request.user, data)
        return Response(
            {
                "detail": "회원 탈퇴 처리가 완료되었습니다. 14일 후 계정이 영구 삭제되며, 그전에 다시 로그인하시면 계정을 복구하실 수 있습니다."
            },
            status=status.HTTP_200_OK,
        )
