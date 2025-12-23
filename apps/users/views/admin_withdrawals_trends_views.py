from typing import Any

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    extend_schema,
    inline_serializer,
)
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.serializers.admin_analytics_serializers import (
    AdminWithdrawalTrendSerializer,
)
from apps.users.services.admin_withdrawals_analytics_services import (
    get_withdrawal_trend,
)
from apps.users.utils.admin_analytics_utils import IntervalLiteral
from apps.users.utils.permissions import StaffOrSuperUser

AdminWithdrawalTrendSimpleErrorSerializer = inline_serializer(
    name="AdminWithdrawalTrendSimpleError",
    fields={
        "error_detail": serializers.CharField(),
    },
)


class AdminWithdrawalTrendSpec(APIView):
    """
    어드민 페이지 회원탈퇴 추세 분석 APIView
    """

    permission_classes = [StaffOrSuperUser]

    @extend_schema(
        tags=["Admin"],
        summary="어드민 페이지 회원탈퇴 추세 분석",
        description="스태프 및 어드민 권한을 가진 유저는 어드민 페이지에서 월별/년별 탈퇴 추세를 조회할 수 있습니다.",
        parameters=[
            OpenApiParameter(
                name="interval",
                type=OpenApiTypes.STR,
                location="query",
                description="집계 단위 (monthly: 월별, yearly: 연도별)",
                enum=["monthly", "yearly"],
            ),
        ],
        responses={
            200: AdminWithdrawalTrendSerializer,
            401: AdminWithdrawalTrendSimpleErrorSerializer,
            403: AdminWithdrawalTrendSimpleErrorSerializer,
        },
        examples=[
            OpenApiExample(
                name="Success Example (Monthly)",
                value={
                    "interval": "monthly",
                    "from_date": "2025-11-01",
                    "to_date": "2025-11-30",
                    "total": 100,
                    "items": [
                        {"period": "2025-11", "count": 100},
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
        params = request.query_params
        interval_raw = params.get("interval")

        if interval_raw not in ("monthly", "yearly"):
            raise ValidationError({"error_detail": "interval 파라미터는 monthly 또는 yearly만 허용됩니다."})

        interval: IntervalLiteral = interval_raw  # type: ignore[assignment]
        trend_result = get_withdrawal_trend(interval=interval)

        serializer = AdminWithdrawalTrendSerializer(trend_result)
        return Response(serializer.data)
