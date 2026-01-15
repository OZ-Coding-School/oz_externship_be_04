from typing import Any

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    extend_schema,
)
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.services.check_nickname_service import nickname_check_service


class NicknameCheckView(APIView):
    permission_classes = (permissions.AllowAny,)

    @extend_schema(
        tags=["Account"],
        summary="닉네임 중복 확인",
        description="닉네임 입력 시 중복된 닉네임이 존재하는지 확인합니다.",
        parameters=[
            OpenApiParameter(
                name="nickname",
                description="중복 확인할 닉네임 입력",
                required=True,
                type=str,
                location=OpenApiParameter.QUERY,
            )
        ],
        methods=["GET"],
        responses={200: OpenApiTypes.OBJECT, 400: OpenApiTypes.OBJECT, 409: OpenApiTypes.OBJECT},
        examples=[
            OpenApiExample(
                response_only=True,
                name="success_case",
                summary="사용 가능",
                value={"detail": "사용가능한 닉네임 입니다."},
                status_codes=["200"],
            ),
            OpenApiExample(
                response_only=True,
                name="nickname_blank",
                summary="입력 누락",
                value={"error_detail": {"nickname": ["이 필드는 필수 항목입니다."]}},
                status_codes=["400"],
            ),
            OpenApiExample(
                response_only=True,
                name="already_exists",
                summary="닉네임 중복",
                value={"error_detail": "중복된 닉네임이 존재합니다."},
                status_codes=["409"],
            ),
        ],
    )
    def get(self, request: Any, *args: Any, **kwargs: Any) -> Response:
        nickname = request.query_params.get("nickname")
        if not nickname:
            return Response(
                {"error_detail": {"nickname": ["이 필드는 필수 항목입니다."]}}, status=status.HTTP_400_BAD_REQUEST
            )

        nickname_check_service(nickname)
        return Response({"detail": "사용가능한 닉네임 입니다."}, status=status.HTTP_200_OK)
