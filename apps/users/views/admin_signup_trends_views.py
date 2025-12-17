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
    AdminSignupTrendSerializer,
)
from apps.users.services.admin_signup_analytics_services import (
    IntervalLiteral,
    get_signup_trend,
)
from apps.users.utils.permissions import StaffOrSuperUser

AdminSignupTrendSimpleErrorSerializer = inline_serializer(
    name="AdminSignupTrendSimpleError",
    fields={
        "error_detail": serializers.CharField(),
    },
)


class AdminSignupTrendView(APIView):
    """
    관리자 및 스태프 전용 회원가입 추세 분석 API
    """

    permission_classes = [StaffOrSuperUser]

    @extend_schema(
        tags=["Admin"],
        summary="어드민 페이지 회원가입 추세 분석",
        description="스태프 및 어드민 권한을 가진 유저는 어드민 페이지에서 월별/년별 회원가입 추세를 조회할 수 있습니다.",
        parameters=[
            OpenApiParameter(
                name="interval",
                type=OpenApiTypes.STR,
                description="집계 간격 (monthly / yearly)",
                enum=["monthly", "yearly"],
            ),
        ],
        responses={
            200: AdminSignupTrendSerializer,
            400: AdminSignupTrendSimpleErrorSerializer,
            403: AdminSignupTrendSimpleErrorSerializer,
        },
        examples=[
            OpenApiExample(
                name="Success Example - Monthly",
                value={
                    "interval": "monthly",
                    "from_date": "2024-12-01",
                    "to_date": "2025-11-30",
                    "total": 100,
                    "items": [
                        {"period": "2024-12", "count": 3},
                        {"period": "2025-01", "count": 5},
                        {"period": "2025-02", "count": 10},
                        {"period": "2025-03", "count": 8},
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

        if interval_raw not in ["monthly", "yearly"]:
            raise ValidationError({"error_detail": "interval 파라미터는 monthly 또는 yearly만 허용됩니다."})

        interval: IntervalLiteral = interval_raw  # type: ignore[assignment]

        trend_result = get_signup_trend(interval=interval)

        serializer = AdminSignupTrendSerializer(trend_result)
        return Response(serializer.data)
