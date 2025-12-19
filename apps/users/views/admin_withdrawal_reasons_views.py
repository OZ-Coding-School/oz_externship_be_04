from typing import Any

from drf_spectacular.utils import OpenApiExample, extend_schema, inline_serializer
from rest_framework import serializers
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.serializers.admin_withdrawals_analytics_serializers import (
    WithdrawalReasonPercentageSerializer,
)
from apps.users.services.admin_withdrawals_analytics_service import (
    get_withdrawal_reason_percentage,
)
from apps.users.utils.permissions import StaffOrSuperUser

AdminWithdrawalAnalyticsSimpleErrorSerializer = inline_serializer(
    name="AdminWithdrawalAnalyticsSimpleError",
    fields={
        "error_detail": serializers.CharField(),
    },
)


class AdminWithdrawalReasonPercentageView(APIView):

    permission_classes = [StaffOrSuperUser]

    @extend_schema(
        tags=["Admin"],
        summary="어드민 페이지 회원 탈퇴 사유 비율 분석",
        description=(
            "스태프 및 관리자 권한을 가진 유저는 어드민 페이지 회원 관리 대시보드에서 "
            "회원 탈퇴 사유 비율을 원형 차트 및 막대 그래프로 확인할 수 있습니다. "
        ),
        responses={
            200: WithdrawalReasonPercentageSerializer,
            401: AdminWithdrawalAnalyticsSimpleErrorSerializer,
            403: AdminWithdrawalAnalyticsSimpleErrorSerializer,
        },
        examples=[
            OpenApiExample(
                name="Success Example",
                value={
                    "from_date": "2020-12-31",
                    "to_date": "2025-11-30",
                    "total": 1945,
                    "items": [
                        {
                            "reason": "OTHER",
                            "reason_label": "기타",
                            "count": 234,
                            "percentage": 12,
                        },
                        {
                            "reason": "LACK_OF_CONTENT",
                            "reason_label": "원하는 콘텐츠나 기능의 부족",
                            "count": 344,
                            "percentage": 17,
                        },
                    ],
                },
                status_codes=["200"],
            ),
            OpenApiExample(
                name="Unauthorized Example",
                value={"error_detail": "자격 인증 데이터가 제공되지 않았습니다."},
                status_codes=["401"],
            ),
            OpenApiExample(
                name="Forbidden Example",
                value={"error_detail": "권한이 없습니다."},
                status_codes=["403"],
            ),
        ],
    )
    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        result = get_withdrawal_reason_percentage()
        serializer = WithdrawalReasonPercentageSerializer(result)
        return Response(serializer.data)
